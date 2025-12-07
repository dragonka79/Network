### Modify the description of the given interface and set its IP address via NETCONF.
    # Rollbacks to previous configuration on failure.

# Pre-check:Fetches current interface configuration via get_config and parses the XML.
            # Compares description and IP; skips changes if already correct.
        
# The interface is administratively down before changes
# IP address and description changes are applied safely
# The interface is brought back up

# NETCONF never crashes (even if the target interface is temporarily down)
# Optional pre-checks to avoid operating on the management interface

# Note: This version does not include saving running-config to startup-config!

from ncclient import manager
from ncclient.operations import RPCError
from lxml import etree
from device_info import device
import xml.dom.minidom

# -----------------------------
# TEMPLATE PATHS
# -----------------------------
SHUT_TEMPLATE_PATH = "/home/zolcs/Network/IOS-XE/ios_shut.xml"
MODIFY_TEMPLATE_PATH = "/home/zolcs/Network/IOS-XE/ios_modify.xml"
NO_SHUT_TEMPLATE_PATH = "/home/zolcs/Network/IOS-XE/ios_no_shut.xml"
ROLLBACK_TEMPLATE_PATH = "/home/zolcs/Network/IOS-XE/ios_rollback.xml"

# -----------------------------
# LOAD TEMPLATES
# -----------------------------
def load_template(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()

shut_template = load_template(SHUT_TEMPLATE_PATH)
modify_template = load_template(MODIFY_TEMPLATE_PATH)
no_shut_template = load_template(NO_SHUT_TEMPLATE_PATH)
rollback_template = load_template(ROLLBACK_TEMPLATE_PATH)

# -----------------------------
# CONFIGURATION PARAMETERS
# -----------------------------
iface_id = "2"
interface_desc = "dragonka_safe_update_via_NETCONF"
ip_address = "192.168.151.99"
subnet_mask = "255.255.255.0"
management_iface = "1"  # e.g., GigabitEthernet1 for management

# -----------------------------
# SAFETY CHECK: Do not touch management interface
# -----------------------------
if iface_id == management_iface:
    raise SystemExit(f"Refusing to modify management interface Gi{iface_id}")

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def push_config(m, xml_payload, step_name):
    print(f"🔹 {step_name} ...")
    reply = m.edit_config(target="running", config=xml_payload)
    try:
        pretty = xml.dom.minidom.parseString(reply.xml.encode()).toprettyxml(indent="  ")
        print(pretty)
    except Exception:
        print(reply)

def get_interface_config(m, iface):
    filter_xml = f"""
    <filter>
      <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
        <interface>
          <GigabitEthernet>
            <name>{iface}</name>
          </GigabitEthernet>
        </interface>
      </native>
    </filter>
    """
    try:
        result = m.get_config(source="running", filter=filter_xml)
        return etree.fromstring(result.xml.encode())
    except RPCError as e:
        print(f"Failed to fetch interface config: {e}")
        return None

def extract_current_values(config_xml):
    """Extract current description, IP, and mask"""
    ns = {"xe": "http://cisco.com/ns/yang/Cisco-IOS-XE-native"}
    desc_elem = config_xml.find(".//xe:description", ns)
    desc = desc_elem.text if desc_elem is not None else ""
    ip_elem = config_xml.find(".//xe:ip/xe:address/xe:primary/xe:address", ns)
    mask_elem = config_xml.find(".//xe:ip/xe:address/xe:primary/xe:mask", ns)
    ip_current = ip_elem.text if ip_elem is not None else ""
    mask_current = mask_elem.text if mask_elem is not None else ""
    return desc, ip_current, mask_current

def needs_change(config_xml):
    """Return True if IP or description differ from desired"""
    desc, ip_current, mask_current = extract_current_values(config_xml)
    if desc != interface_desc or ip_current != ip_address or mask_current != subnet_mask:
        return True
    return False

# -----------------------------
# FORMAT TEMPLATES
# -----------------------------
shut_config = shut_template.format(iface_id=iface_id)
modify_config = modify_template.format(
    iface_id=iface_id,
    interface_desc=interface_desc,
    ip_address=ip_address,
    subnet_mask=subnet_mask
)
no_shut_config = no_shut_template.format(iface_id=iface_id)

# -----------------------------
# CONNECT AND EXECUTE SEQUENCE WITH ROLLBACK
# -----------------------------
try:
    with manager.connect(
        host=device["host"],
        port=int(device.get("port", 830)),
        username=device["username"],
        password=device["password"],
        hostkey_verify=False,
        timeout=30
    ) as m:

        # Fetch current interface config
        current_config = get_interface_config(m, iface_id)
        if current_config is None:
            raise SystemExit("Cannot fetch interface config. Aborting.")

        # Determine if change is needed
        if not needs_change(current_config):
            print(f"Interface Gi{iface_id} already has desired IP and description. No changes needed.")
        else:
            # Extract current values for rollback
            old_desc, old_ip, old_mask = extract_current_values(current_config)
            rollback_config = rollback_template.format(
                iface_id=iface_id,
                interface_desc=old_desc,
                ip_address=old_ip,
                subnet_mask=old_mask
            )

            try:
                # 1️⃣ Shut interface
                push_config(m, shut_config, "Shutting interface")

                # 2️⃣ Apply modifications
                push_config(m, modify_config, "Modifying interface")

                # 3️⃣ Bring interface back up
                push_config(m, no_shut_config, "Bringing interface up")

            except Exception as e:
                print(f"Modification failed: {e}. Rolling back previous configuration.")
                push_config(m, rollback_config, "Rolling back interface config")
                push_config(m, no_shut_config, "Bringing interface up after rollback")
                raise

except Exception as e:
    print(f"NETCONF operation failed: {e}")

