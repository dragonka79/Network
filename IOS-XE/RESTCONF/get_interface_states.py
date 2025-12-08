import requests
import json
from device_info import device
from requests.exceptions import RequestException

requests.packages.urllib3.disable_warnings()

# set REST API headers
headers = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json",
}

interface = "GigabitEthernet2"
url = f"https://{device['host']}:{device['port']}/restconf/data/Cisco-IOS-XE-interfaces-oper:interfaces/interface={interface}"

# use a session, add timeout and error handling, and access fields safely
session = requests.Session()
session.headers.update(headers)

try:
    resp = session.get(url, auth=(device['username'], device['password']), verify=False, timeout=10)
    resp.raise_for_status()
    api_data = resp.json()
except RequestException as e:
    print(f"Request failed: {e}")
    raise SystemExit(1)
except ValueError:
    print("Failed to decode JSON response")
    raise SystemExit(1)

# safe extraction of the interface container
iface = api_data.get("Cisco-IOS-XE-interfaces-oper:interface", {})

description = iface.get("description") or "N/A"

# normalize admin-status to human-friendly form
raw_admin = iface.get("admin-status") or iface.get("admin_state") or ""
raw_admin_lower = str(raw_admin).lower()
if "up" in raw_admin_lower:
    admin_state = "up"
elif "down" in raw_admin_lower:
    admin_state = "down"
elif raw_admin:
    admin_state = raw_admin  # fallback to raw value
else:
    admin_state = "N/A"

# normalize oper-status to human-friendly form
raw_oper = iface.get("oper-status") or iface.get("oper_state") or ""
raw_oper_lower = str(raw_oper).lower()
if "ready" in raw_oper_lower:
    oper_state = "up"
elif "no-pass" in raw_oper_lower:
    oper_state = "down"
elif raw_oper:
    oper_state = raw_oper  # fallback to raw value
else:
    oper_state = "N/A"

print("/" * 50)
print(f"Interface: {interface}")
print("/" * 50)
print(f"Description: {description}")
print("/" * 50)
if admin_state == "up":
    print(f"Interface is admin up")
else:
    print(f"Interface admin-state: {admin_state}")
print("/" * 50)
if oper_state == "up":
    print(f"Interface is operational up")
else:
    print(f"Interface oper-state: {oper_state}")