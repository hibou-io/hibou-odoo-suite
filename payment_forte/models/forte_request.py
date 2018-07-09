from base64 import b64encode
from json import dumps
import requests


class ForteAPI:

    url_prod = 'https://api.forte.net/v3'
    url_test = 'https://sandbox.forte.net/api/v3'

    def __init__(self, organization_id, access_id, secure_key, environment):
        self.organization_id = organization_id
        self.access_id = access_id
        self.secure_key = secure_key
        self.basic_key = b64encode(bytes(access_id + ':' + secure_key, 'UTF-8')).decode()
        self.environment = environment
        self.headers = {
                'Content-Type': 'application/json',
                'X-Forte-Auth-Organization-Id': 'org_' + self.organization_id,
                'Authorization': 'Basic ' + self.basic_key,
            }

    def _build_request(self, location, method, data=None):
        url = self.url_prod
        if self.environment == 'test':
            url = self.url_test
        url += location
        return requests.request(method, url, headers=self.headers, data=data)

    def test_authenticate(self, location=None):
        if location:
            url = '/organizations/org_%s/locations/loc_%s/transactions/' % (self.organization_id, location)
        else:
            url = '/organizations/org_%s/transactions/' % (self.organization_id, )
        return self._build_request(url, 'GET')

    def _echeck_values(self, location, amount, account_type, routing_number, account_number, account_holder):
        #{
        #   "action": "sale",
        #   "authorization_amount": 200.0,
        #   "billing_address": {
        #     "first_name": "Jared",
        #     "last_name": "Kipe"},
        #   "echeck": {
        #     "sec_code": "WEB",
        #     "account_type": "Checking",
        #     "routing_number": "021000021",
        #     "account_number": "000111222",
        #     "account_holder": "Jared Kipe"}
        #}
        holder_array = account_holder.strip().split()
        first_name = ''
        last_name = holder_array[-1]
        if len(holder_array) >= 2:
            first_name = ' '.join(holder_array[:-1])
        data = {
            'action': 'sale',
            'authorization_amount': amount,
            'billing_address': {
                'first_name': first_name,
                'last_name': last_name,
            },
            'echeck': {
                'sec_code': 'WEB',
                'account_type': account_type,
                'routing_number': routing_number,
                'account_number': account_number,
                'account_holder': account_holder,
            },
        }
        url = '/organizations/org_%s/locations/loc_%s/transactions/' % (self.organization_id, location)
        return url, data

    def echeck_sale(self, location, amount, account_type, routing_number, account_number, account_holder):
        url, data = self._echeck_values(location, amount, account_type, routing_number, account_number, account_holder)
        return self._build_request(url, 'POST', data=dumps(data))

    def echeck_credit(self, location, amount, account_type, routing_number, account_number, account_holder):
        url, data = self._echeck_values(location, amount, account_type, routing_number, account_number, account_holder)
        data['action'] = 'credit'
        return self._build_request(url, 'POST', data=dumps(data))
