from base64 import b64encode
import requests

API_URL = 'https://api.signifyd.com/v3'


class SignifydAPI:
    _teamid = None
    _key = None

    def __init__(self, key, teamid):
        self._key = b64encode(key.encode()).decode().strip('=')
        self._teamid = teamid

    def _get_headers(self):
        headers = {
            'Authorization': 'Basic ' + self._key,
            'Content-Type': 'application/json',
        }
        return headers

    def _request(self, method, path, headers=None, json=None):
        request_headers = {
            **(headers or {}),
            **self._get_headers()
        }
        request = requests.request(method, API_URL + path, headers=request_headers, json=json)
        return request

    def get(self, path, headers=None):
        return self._request('GET', path, headers=headers)

    def post(self, path, headers=None, json=None):
        return self._request('POST', path, headers=headers, json=json)

    def post_case(self, values):
        # data = json.dumps(values, indent=4, sort_keys=True, default=str)
        r = self.post('/orders/events/sales', json=values)
        return r.json()

    def get_decision(self, case_id):
        return self.get(f'/orders/{case_id}/decision')

    def register_webhook(self, url):
        return self.post(f"/teams/{self._teamid}/webhooks", json={'url': url})

    def test_webhook(self, url):
        #  https://api.signifyd.com/v3/webhooks/tests
        return self.post('/webhooks/tests', json={'url': url})