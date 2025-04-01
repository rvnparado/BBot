import requests
import json
import urllib3
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.poolmanager import PoolManager
import ssl

# Disable SSL verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        """Create and initialize the urllib3 PoolManager."""
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_version=ssl.PROTOCOL_TLSv1_2,
            ssl_context=ctx
        )


# Configure retries
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)

# Create session with custom SSL adapter
session = requests.Session()
adapter = TLSAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

# Webhook configuration
url = "https://fcda-103-183-193-140.ngrok-free.app/webhook"
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

data = {
    "side": "long",
    "symbol": "BTCUSDT",
    "tp": 88000,
    "sl": 80000,
}

print(f"Sending request to: {url}")
print(f"Request data: {json.dumps(data, indent=2)}")

try:
    response = session.post(url, headers=headers, json=data, verify=False)
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
except requests.exceptions.RequestException as e:
    print(f"Error sending request: {str(e)}")
