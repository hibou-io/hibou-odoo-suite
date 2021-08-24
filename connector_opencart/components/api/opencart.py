# © 2019 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import requests
from urllib.parse import urlencode
from json import loads, dumps
from json.decoder import JSONDecodeError

import logging
_logger = logging.getLogger(__name__)


class Opencart:

    def __init__(self, base_url, restadmin_token):
        self.base_url = str(base_url) + '/api/rest_admin/'
        self.restadmin_token = restadmin_token
        self.session = requests.Session()
        self.session.headers['X-Oc-Restadmin-Id'] = self.restadmin_token

    @property
    def orders(self):
        return Orders(connection=self)

    @property
    def stores(self):
        return Stores(connection=self)

    @property
    def products(self):
        return Products(connection=self)

    def get_headers(self, url, method):
        headers = {}
        if method in ('POST', 'PUT', ):
            headers['Content-Type'] = 'application/json'
        return headers

    def send_request(self, method, url, params=None, body=None):
        encoded_url = url
        if params:
            encoded_url += '?%s' % urlencode(params)
        headers = self.get_headers(encoded_url, method)
        _logger.debug('send_request method: %s url: %s headers: %s params: %s body: %s' % (
            method,
            url,
            headers,
            params,
            body
        ))
        if method == 'GET':
            result_text = self.session.get(url, params=params, headers=headers).text
        elif method == 'PUT' or method == 'POST':
            result_text = self.session.put(url, data=body, headers=headers).text
        _logger.debug('raw_text: ' + str(result_text))
        try:
            return loads(result_text)
        except JSONDecodeError:
            return {}


class Resource:
    """
    A base class for all Resources to extend
    """

    def __init__(self, connection):
        self.connection = connection

    @property
    def url(self):
        return self.connection.base_url + self.path


class Orders(Resource):
    """
    Retrieves Order details
    """

    path = 'orders'

    def all(self, id_larger_than=None, modified_from=None):
        url = self.url
        if id_larger_than:
            url += '/id_larger_than/%s' % id_larger_than
        if modified_from:
            url += '/modified_from/%s' % modified_from
        return self.connection.send_request(method='GET', url=url)

    def get(self, id):
        url = self.url + ('/%s' % id)
        return self.connection.send_request(method='GET', url=url)

    def ship(self, id, tracking, tracking_comment=None):
        def url(stem):
            return self.connection.base_url + ('%s/%s' % (stem, id))
        res = self.connection.send_request(method='PUT', url=url('trackingnumber'), body=self.get_tracking_payload(tracking))
        if tracking_comment:
            res = self.connection.send_request(method='PUT', url=url('orderhistory'), body=self.get_orderhistory_payload(
                3,  # "Shipped"
                True,  # Notify!
                tracking_comment,
            ))
        return res

    def cancel(self, id):
        url = self.connection.base_url + ('order_status/%s' % id)
        return self.connection.send_request(method='POST', url=url, body=self.get_status_payload('Canceled'))

    def get_status_payload(self, status):
        """
        {
          "status": "Canceled"
        }
        """
        payload = {
            "status": status,
        }
        return dumps(payload)

    def get_tracking_payload(self, tracking):
        """
        {
          "tracking": "5559994444"
        }
        """
        payload = {
            "tracking": tracking,
        }
        return dumps(payload)

    def get_orderhistory_payload(self, status_id, notify, comment):
        """
        {
          "order_status_id": "5",
          "notify": "1",
          "comment": "demo comment"
        }
        """
        payload = {
            'order_status_id': str(status_id),
            'notify': '1' if notify else '0',
            'comment': str(comment)
        }
        return dumps(payload)


class Stores(Resource):
    """
    Retrieves Store details
    """

    path = 'stores'

    def all(self):
        return self.connection.send_request(method='GET', url=self.url)

    def get(self, id):
        url = self.url + ('/%s' % id)
        return self.connection.send_request(method='GET', url=url)


class Products(Resource):
    """
    Retrieves Product details
    """
    path = 'products'

    def get(self, id):
        url = self.url + ('/%s' % id)
        return self.connection.send_request(method='GET', url=url)
