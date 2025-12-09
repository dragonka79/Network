import json
from pprint import pprint
import requests
from get_token import cookies, HOST, VERIFY, TIMEOUT

requests.packages.urllib3.disable_warnings()  # keep for lab; prefer proper CA bundle in production

intf = "eth1/2"
descr = "SampleString_12345678"

URL = f"https://{HOST}/api/mo/sys/intf/phys-[{intf}].json"
method = "POST"


payload = json.dumps({
  "l1PhysIf": {
    "attributes": {
      "id": intf,
      "descr": descr
    }
  }
})

headers = {
  'Content-Type': 'application/json'
}

response = requests.request(method, URL, headers=headers, cookies=cookies, data=payload, verify=VERIFY, timeout=TIMEOUT).json()
pprint(response)

