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

    def _request(self, method, path, headers=None, json=None):
        headers = headers or {}
        headers.update(self._get_headers())
        request = requests.request(method, API_URL + path, headers=headers, json=json)
        return request

    def get(self, path, headers=None):
        return self._request('GET', path, headers=headers)

    def post(self, path, headers=None, json=None):
        return self._request('POST', path, headers=headers, json=json)

    def post_case(self, connector, values):
        # data = json.dumps(values, indent=4, sort_keys=True, default=str)
        r = self._post('/orders/events/sales', json=values)
        return r.json()
