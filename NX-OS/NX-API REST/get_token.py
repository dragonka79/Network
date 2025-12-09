import os
import json
from pprint import pprint
import requests
from pathlib import Path
from requests.exceptions import RequestException, Timeout
from device_info import device

requests.packages.urllib3.disable_warnings()  # keep for lab; prefer proper CA bundle in production

# Use device_info values
HOST = device.get("host", "127.0.0.1")
USER = device.get("username", "admin")
PWD = device.get("password", "")
VERIFY = device.get("verify", False)
TIMEOUT = float(device.get("timeout", 10))

# Optional token file via env (keeps script generic)
TOKEN_FILE = os.getenv("ACI_TOKEN_FILE")

URL = f"https://{HOST}/api/aaaLogin.json"

def safe_get(dct, *keys):
    cur = dct
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur

payload = {"aaaUser": {"attributes": {"name": USER, "pwd": PWD}}}

session = requests.Session()
session.headers.update({"Content-Type": "application/json"})

try:
    resp = session.post(URL, json=payload, verify=VERIFY, timeout=TIMEOUT)
    resp.raise_for_status()
    try:
        data = resp.json()
    except ValueError:
        raise SystemExit("Invalid JSON received from APIC")

    # common APIC token path
    token = None
    imdata = safe_get(data, "imdata")
    if isinstance(imdata, list) and imdata:
        token = safe_get(imdata[0], "aaaLogin", "attributes", "token")

    token = token or safe_get(data, "token") or safe_get(data, "aaaLogin", "token")

    if token:
        masked = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "****"
        print("Token obtained:", masked)

        if TOKEN_FILE:
            tf = Path(TOKEN_FILE).expanduser()
            tf.parent.mkdir(parents=True, exist_ok=True)
            with tf.open("w", encoding="utf-8") as fh:
                fh.write(token + "\n")
            try:
                tf.chmod(0o600)
            except Exception:
                pass
            print("Token saved to:", str(tf))
    else:
        print("Authentication succeeded but token not found in response.")
except Timeout:
    print("Request timed out")
except RequestException as e:
    print(f"Request failed: {e}")

cookies = {'APIC-cookie': token} if token else {}
