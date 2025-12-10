## Settings for NX-API CLI and REST interaction to get CDP neighbors and update interface descriptions accordingly

######################################  LOGIN WITH NX-API CLI  ######################################

import re
import requests
import json
from pathlib import Path
from device_info import device

requests.packages.urllib3.disable_warnings()

switch_ip_address = device["host"]
switchuser = device["username"]
switchpassword = device["password"]

url = f"https://{switch_ip_address}/ins"
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

payload = {
    "ins_api": {
        "version": "1.0",
        "type": "cli_show",
        "chunk": "0",
        "sid": "1",
        "input": "show cdp neighbors",
        "output_format": "json"
    }
}

# output file named after this python file with _result.txt suffix
# OUTPUT_PATH = Path(__file__).with_name(Path(__file__).stem + "_result").with_suffix('.txt')

try:
    resp = requests.post(
        url,
        headers=headers,
        auth=(switchuser, switchpassword),
        data=json.dumps(payload),
        verify=False,
        timeout=10
    )

    resp.raise_for_status()

    # try to decode JSON, fallback to raw text
    try:
        data = resp.json()
        pretty = json.dumps(data, indent=4)
    except ValueError:
        pretty = resp.text or ""

    # print to console
    print(pretty)

    # # save to file
    # with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
    #     fh.write(pretty + "\n")

    # print(f"Saved output to: {OUTPUT_PATH}")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")

######################################  LOGIN WITH NX-API REST  ######################################

auth_url = f"https://{switch_ip_address}/api/aaaLogin.json"
auth_body = {
    "aaaUser": {
        "attributes": {
            "name": switchuser,
            "pwd": switchpassword
        }
    }
}   

auth_resp = requests.post(
    auth_url,
    headers=headers,
    data=json.dumps(auth_body),
    verify=False,
    timeout=10
).json()
token = auth_resp["imdata"][0]["aaaLogin"]["attributes"]["token"]
cookies = {'APIC-cookie': token}

counter = 0
nei_count = data['ins_api']['outputs']['output']['body']['neigh_count']
print(f"Number of CDP Neighbors: {nei_count}")

while counter < int(nei_count):
    neighbor = data['ins_api']['outputs']['output']['body']['TABLE_cdp_neighbor_brief_info']['ROW_cdp_neighbor_brief_info'][counter]['device_id']
    local_interface = data['ins_api']['outputs']['output']['body']['TABLE_cdp_neighbor_brief_info']['ROW_cdp_neighbor_brief_info'][counter]['intf_id']
    remote_interface = data['ins_api']['outputs']['output']['body']['TABLE_cdp_neighbor_brief_info']['ROW_cdp_neighbor_brief_info'][counter]['port_id']
    
    body = {
        "l1PhysIf": {
            "attributes": {
                "descr": f"Connected to {neighbor} via {remote_interface}"
            }
        }
    } 
    counter += 1
    
    if local_interface.lower() != "mgmt0":

        # Normalize interface name: Eth1/2 → eth1/2
        m = re.search(r'(eth|ethernet)?\s*(\d+/\d+(?:/\d+)*)', local_interface, re.IGNORECASE)

        if not m:
            print(f"Skipping invalid interface format: {local_interface}")
            continue

        int_name = "eth"
        int_number = m.group(2)

        full_int = f"{int_name}{int_number}"

        int_url = f"https://{switch_ip_address}/api/node/mo/sys/intf/phys-[{full_int}].json"

        print(f"Updating interface: {full_int}")

        post_resp = requests.post(
            int_url,
            headers=headers,
            cookies=cookies,
            data=json.dumps(body),
            verify=False,
            timeout=10
        ).json()

        print(json.dumps(post_resp, indent=4))
