import requests
import json
from requests.exceptions import RequestException, Timeout
from device_info import device
from pathlib import Path

requests.packages.urllib3.disable_warnings()  # keep for lab; prefer proper CA bundle in production

HOST = device["host"]
PORT = device.get("port", 443)
USERNAME = device["username"]
PASSWORD = device["password"]

URL = f"https://{HOST}:{PORT}/ins"
OUTPUT_PATH = str(Path(__file__).with_name(Path(__file__).stem + "_result").with_suffix('.txt'))

HEADERS = {"Content-Type": "application/json"}

# Commands to run (safe single string for NX-API cli_show)
commands = "show version ; show ip interface brief ; show interface status"

payload = {
    "ins_api": {
        "version": "1.0",
        "type": "cli_show",
        "chunk": "0",
        "sid": "1",
        "input": commands,
        "output_format": "json",
    }
}

# allow verification and timeout to be configured in device_info (verify can be bool or path to CA bundle)
VERIFY = device.get("verify", False)
TIMEOUT = float(device.get("timeout", 10))

session = requests.Session()
session.headers.update(HEADERS)
session.auth = (USERNAME, PASSWORD)

try:
    resp = session.post(URL, json=payload, verify=VERIFY, timeout=TIMEOUT)
    resp.raise_for_status()
    try:
        pretty = json.dumps(resp.json(), indent=2)
    except ValueError:
        pretty = resp.text
    # print to console (no credentials)
    print(pretty)
    # save to file
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(pretty + "\n")
    print(f"Saved output to: {OUTPUT_PATH}")
except Timeout:
    print("Request timed out")
except RequestException as e:
    # do not leak credentials in error messages
    print(f"Request failed: {e}")
