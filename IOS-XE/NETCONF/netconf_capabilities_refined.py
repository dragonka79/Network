### Getting device capabilities and interface info via NETCONF on IOS-XE device
### Modules netconf-filter.xml and device_info.py are used here

from ncclient import manager
from pprint import pprint
import xmltodict
import xml.dom.minidom
from device_info import device
from datetime import datetime

def _text(node):
    """Return text from xmltodict node safely."""
    if node is None:
        return None
    if isinstance(node, dict):
        return node.get('#text') or node.get('text') or None
    return str(node)

def safe_get(dct, *keys):
    """Safe nested get for dictionaries; returns None if any key is missing."""
    cur = dct
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur

def human_readable_bytes(value):
    """Convert a bytes value (int or numeric string) to a human readable string."""
    if value is None:
        return 'N/A'
    try:
        n = int(str(value).strip())
    except Exception:
        return 'N/A'
    # Use 1000 base for KB/MB/GB
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    idx = 0
    while n >= 1000 and idx < len(units) - 1:
        n /= 1000.0
        idx += 1
    # Show bytes as integer, others with 2 decimals
    if units[idx] == 'B':
        return f"{int(n)} {units[idx]}"
    return f"{n:.2f} {units[idx]}"

def format_last_change(value):
    """
    Convert ISO8601 timestamp (e.g. 2025-12-07T09:38:00.000635+00:00)
    to human readable form: DD-MM-YYYY  HH-MM-SS <Timezone>
    Example: 07-12-2025  09-38-00 +00:00
    """
    if not value:
        return 'N/A'
    try:
        # handle trailing 'Z' as UTC
        s = value.strip()
        if s.endswith('Z'):
            s = s[:-1] + '+00:00'
        dt = datetime.fromisoformat(s)
    except Exception:
        return value  # fallback to raw string if parsing fails

    tz = dt.isoformat()[-6:] if dt.tzinfo else ''
    formatted = dt.strftime('%d-%m-%Y  %H-%M-%S')
    return f"{formatted} {tz}" if tz else formatted

# path to save only the final printed output lines
OUTPUT_PATH = f"/home/zolcs/Network/IOS-XE/NETCONF/netconf_capabilites_result_{device['host']}.txt"

netconf_filter = open("/home/zolcs/Network/IOS-XE/NETCONF/netconf-filter.xml").read()

def log(msg=""):
    """Console-only logging; do NOT collect these lines for file output."""
    print(str(msg))

with manager.connect(
    host=device["host"],
    port=device["port"],
    username=device["username"],
    password=device["password"],
    hostkey_verify=False
) as m:
    for capability in m.server_capabilities:
        log('*' * 50)
        log(capability)
    log('Connected')
    interface_netconf = m.get(netconf_filter)
    log('getting running config')

# XMLDOM for formatting output to xml (console only)
try:
    xmlDom = xml.dom.minidom.parseString(interface_netconf.xml)
    print(xmlDom.toprettyxml(indent="  "))
except Exception:
    try:
        print(str(interface_netconf))
    except Exception:
        print("Failed to pretty print NETCONF reply")

print('*' * 25 + 'Break' + '*' * 50)

# XMLTODICT for converting xml output to a python dictionary
try:
    interface_python = xmltodict.parse(interface_netconf.xml)["rpc-reply"]["data"]
except Exception as e:
    print("Failed to parse NETCONF reply to dict:", e)
    interface_python = {}

pprint(interface_python)

# locate configuration and operational state safely
config = safe_get(interface_python, "interfaces", "interface") or {}
op_state = safe_get(interface_python, "interfaces-state", "interface") or {}

# safe extractions
name = _text(config.get('name')) or 'N/A'
description = _text(config.get('description')) or 'N/A'

packets_in = 'N/A'
try:
    stats = op_state.get('statistics') if isinstance(op_state, dict) else None
    packets_in_val = _text(stats.get('in-unicast-pkts')) if stats else None
    if packets_in_val:
        packets_in = packets_in_val
except Exception:
    packets_in = 'N/A'

admin_state = _text(op_state.get('admin-status')) or 'N/A'
oper_state = _text(op_state.get('oper-status')) or 'N/A'
# format last-change to human readable form
raw_last_change = _text(op_state.get('last-change')) or None
last_change = format_last_change(raw_last_change)
phys_address = _text(op_state.get('phys-address')) or 'N/A'
raw_speed = _text(op_state.get('speed')) or None
speed = human_readable_bytes(raw_speed)

# final printed/result lines (these are the ONLY lines saved to OUTPUT_PATH)
result_lines = [
    f"Host: {device['host']}",
    f"Name: {name}",
    f"Description: {description}",
    f"Packets In: {packets_in}",
    f"Admin-state: {admin_state}",
    f"Oper-state: {oper_state}",
    f"Last-change: {last_change}",
    f"phys-address: {phys_address}",
    f"speed: {speed}",
]

# print to console
for line in result_lines:
    print(line)

# save ONLY the final printed result lines to file
try:
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(result_lines) + "\n")
    print(f"Saved result lines to: {OUTPUT_PATH}")
except Exception as e:
    print(f"Failed to save result lines to {OUTPUT_PATH}: {e}")
