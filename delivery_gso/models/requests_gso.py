import requests
from json import dumps


class GSORequest:

    BASE_URL = 'https://api.gso.com/Rest/v1'

    def __init__(self, production, username, password, account_number):
        self.username = username
        self.password = password
        self.account_number = account_number
        self.headers = self.make_headers()
        self._get_token()

    def make_headers(self):
        return {
            'Content-Type': 'application/json',
            'Accept-Encoding': 'gzip',
            'UserName': self.username,
            'PassWord': self.password,
            'AccountNumber': self.account_number,
        }

    # Token Lasts 12 hours and should be refreshed accordingly.
    # Might need to change to prevent too many calls to the API
    def _get_token(self):
        endpoint_url = self.BASE_URL + '/token'
        response = requests.get(endpoint_url, headers=self.headers)
        response.raise_for_status()
        self.headers.update({'Token': response.headers['Token']})

    def call(self, http_method, endpoint_url, payload):
        url = self.BASE_URL + endpoint_url
        result = requests.request(http_method, url, data=dumps(payload), headers=self.headers)
        if result.status_code != 200:
            raise requests.exceptions.HTTPError(result.text)
        return result.json()

    def post_shipment(self, request_body):
        return self.call('POST', '/Shipment', request_body)

    def delete_shipment(self, request_body):
        return self.call('DELETE', '/Shipment', request_body)

    def get_rates_and_transit_time(self, request_body):
        return self.call('POST', '/RatesAndTransitTimes', request_body)
