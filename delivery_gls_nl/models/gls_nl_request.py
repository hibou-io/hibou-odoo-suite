# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import requests
from json import dumps


class GLSNLRequest:
    def __init__(self, production):
        self.production = production
        self.api_key = '234a6d4ad5fd4d039526a8a1074051ee' if production else 'f80d41c6f7d542878c9c0a4295de7a6a'
        self.url = 'https://api.gls.nl/V1/api' if production else 'https://api.gls.nl/Test/V1/api'
        self.headers = self._make_headers()

    def _make_headers(self):
        return {
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': self.api_key,
        }

    def post_request(self, endpoint, body):
        if not self.production and body.get('username') == 'test':
            # Override to test credentials
            body['username'] = 'apitest1@gls-netherlands.com'
            body['password'] = '9PMev9qM'
        url = self.url + endpoint
        result = requests.request('POST', url, headers=self.headers, data=dumps(body))
        if result.status_code != 200:
            raise requests.HTTPError(result.text)
        return result.json()

    def create_label(self, body):
        return self.post_request('/Label/Create', body)

    def confirm_label(self, body):
        return self.post_request('/Label/Confirm', body)

    def delete_label(self, body):
        return self.post_request('/Label/Delete', body)
