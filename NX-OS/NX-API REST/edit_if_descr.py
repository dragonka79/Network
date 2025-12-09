import json
from pprint import pprint
import requests
from requests.exceptions import RequestException, Timeout
from urllib.parse import quote
from get_token import cookies, HOST, VERIFY, TIMEOUT

requests.packages.urllib3.disable_warnings()  # for lab use; use proper CA bundle in production

# small input validation / sanitization
intf = "eth1/2"
descr = "SampleString_123456789"

if not isinstance(intf, str) or not intf.strip():
    raise SystemExit("Invalid interface name")

# limit description length and strip non-printable characters
descr = ''.join(ch for ch in str(descr) if ch.isprintable())[:255]

intf_esc = quote(intf, safe='')  # escape special chars for URL
URL = f"https://{HOST}/api/mo/sys/intf/phys-[{intf_esc}].json"

payload = {
  "l1PhysIf": {
    "attributes": {
      "id": intf,
      "descr": descr
    }
  }
}

# use a session with cookies and proper headers
session = requests.Session()
session.cookies.update(cookies or {})
session.headers.update({'Content-Type': 'application/json'})

try:
    resp = session.post(URL, json=payload, verify=VERIFY, timeout=TIMEOUT)
    resp.raise_for_status()
    try:
        data = resp.json()
    except ValueError:
        print("Non-JSON response received")
        print(resp.text)
    else:
        # pretty-print response (do not leak sensitive fields)
        pprint(data)
except Timeout:
    print("Request timed out")
except RequestException as e:
    # avoid printing secrets in errors
    print(f"Request failed: {e}")
