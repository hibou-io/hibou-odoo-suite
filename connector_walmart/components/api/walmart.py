# -*- coding: utf-8 -*-

# BSD License
#
# Copyright (c) 2016, Fulfil.IO Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice, this
#   list of conditions and the following disclaimer in the documentation and/or
#   other materials provided with the distribution.
#
# * Neither the name of Fulfil nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.

# © 2017 Hibou Corp. - Extended and converted to v3/JSON


import requests
import base64
import time
from uuid import uuid4
# from lxml import etree
# from lxml.builder import E, ElementMaker
from json import dumps, loads

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode


class Walmart(object):

    def __init__(self, consumer_id, channel_type, private_key):
        self.base_url = 'https://marketplace.walmartapis.com/v3/%s'
        self.consumer_id = consumer_id
        self.channel_type = channel_type
        self.private_key = private_key
        self.session = requests.Session()
        self.session.headers['Accept'] = 'application/json'
        self.session.headers['WM_SVC.NAME'] = 'Walmart Marketplace'
        self.session.headers['WM_CONSUMER.ID'] = self.consumer_id
        self.session.headers['WM_CONSUMER.CHANNEL.TYPE'] = self.channel_type

    @property
    def items(self):
        return Items(connection=self)

    @property
    def inventory(self):
        return Inventory(connection=self)

    @property
    def prices(self):
        return Prices(connection=self)

    @property
    def orders(self):
        return Orders(connection=self)

    def get_sign(self, url, method, timestamp):
        return self.sign_data(
            '\n'.join([self.consumer_id, url, method, timestamp]) + '\n'
        )

    def sign_data(self, data):
        rsakey = RSA.importKey(base64.b64decode(self.private_key))
        signer = PKCS1_v1_5.new(rsakey)
        digest = SHA256.new()
        digest.update(data.encode('utf-8'))
        sign = signer.sign(digest)
        return base64.b64encode(sign)

    def get_headers(self, url, method):
        timestamp = str(int(round(time.time() * 1000)))
        headers = {
            'WM_SEC.AUTH_SIGNATURE': self.get_sign(url, method, timestamp),
            'WM_SEC.TIMESTAMP': timestamp,
            'WM_QOS.CORRELATION_ID': str(uuid4()),
        }
        if method in ('POST', ):
            headers['Content-Type'] = 'application/json'
        return headers

    def send_request(self, method, url, params=None, body=None):
        encoded_url = url
        if params:
            encoded_url += '?%s' % urlencode(params)
        headers = self.get_headers(encoded_url, method)

        if method == 'GET':
            return loads(self.session.get(url, params=params, headers=headers).text)
        elif method == 'PUT':
            return loads(self.session.put(url, params=params, headers=headers).text)
        elif method == 'POST':
            return loads(self.session.post(url, data=body, headers=headers).text)


class Resource(object):
    """
    A base class for all Resources to extend
    """

    def __init__(self, connection):
        self.connection = connection

    @property
    def url(self):
        return self.connection.base_url % self.path

    def all(self, **kwargs):
        return self.connection.send_request(
            method='GET', url=self.url, params=kwargs)

    def get(self, id):
        url = self.url + '/%s' % id
        return self.connection.send_request(method='GET', url=url)

    def update(self, **kwargs):
        return self.connection.send_request(
            method='PUT', url=self.url, params=kwargs)

    # def bulk_update(self, items):
    #     url = self.connection.base_url % 'feeds?feedType=%s' % self.feedType
    #     return self.connection.send_request(
    #         method='POST', url=url, data=self.get_payload(items))


class Items(Resource):
    """
    Get all items
    """

    path = 'items'


class Inventory(Resource):
    """
    Retreives inventory of an item
    """

    path = 'inventory'
    feedType = 'inventory'

    def get_payload(self, items):
        return etree.tostring(
            E.InventoryFeed(
                E.InventoryHeader(E('version', '1.4')),
                *[E(
                    'inventory',
                    E('sku', item['sku']),
                    E(
                        'quantity',
                        E('unit', 'EACH'),
                        E('amount', item['quantity']),
                    )
                ) for item in items],
                xmlns='http://walmart.com/'
            )
        )


class Prices(Resource):
    """
    Retreives price of an item
    """

    path = 'prices'
    feedType = 'price'

    def get_payload(self, items):
        # root = ElementMaker(
        #     nsmap={'gmp': 'http://walmart.com/'}
        # )
        # return etree.tostring(
        #     root.PriceFeed(
        #         E.PriceHeader(E('version', '1.5')),
        #         *[E.Price(
        #             E(
        #                 'itemIdentifier',
        #                 E('sku', item['sku'])
        #             ),
        #             E(
        #                 'pricingList',
        #                 E(
        #                     'pricing',
        #                     E(
        #                         'currentPrice',
        #                         E(
        #                             'value',
        #                             **{
        #                                 'currency': item['currenctCurrency'],
        #                                 'amount': item['currenctPrice']
        #                             }
        #                         )
        #                     ),
        #                     E('currentPriceType', item['priceType']),
        #                     E(
        #                         'comparisonPrice',
        #                         E(
        #                             'value',
        #                             **{
        #                                 'currency': item['comparisonCurrency'],
        #                                 'amount': item['comparisonPrice']
        #                             }
        #                         )
        #                     ),
        #                     E(
        #                         'priceDisplayCode',
        #                         **{
        #                             'submapType': item['displayCode']
        #                         }
        #                     ),
        #                 )
        #             )
        #         ) for item in items]
        #     ), xml_declaration=True, encoding='utf-8'
        # )
        payload = {}
        return


class Orders(Resource):
    """
    Retrieves Order details
    """

    path = 'orders'

    def all(self, **kwargs):
        next_cursor = kwargs.pop('nextCursor', '')
        return self.connection.send_request(
            method='GET', url=self.url + next_cursor, params=kwargs)

    def released(self, **kwargs):
        next_cursor = kwargs.pop('nextCursor', '')
        url = self.url + '/released'
        return self.connection.send_request(
            method='GET', url=url + next_cursor, params=kwargs)

    def acknowledge(self, id):
        url = self.url + '/%s/acknowledge' % id
        return self.connection.send_request(method='POST', url=url)

    def cancel(self, id, lines):
        url = self.url + '/%s/cancel' % id
        return self.connection.send_request(
            method='POST', url=url, body=self.get_cancel_payload(lines))

    def get_cancel_payload(self, lines):
        """
        {
          "orderCancellation": {
            "orderLines": {
              "orderLine": [
                {
                  "lineNumber": "1",
                  "orderLineStatuses": {
                    "orderLineStatus": [
                      {
                        "status": "Cancelled",
                        "cancellationReason": "CUSTOMER_REQUESTED_SELLER_TO_CANCEL",
                        "statusQuantity": {
                          "unitOfMeasurement": "EA",
                          "amount": "1"
                        }
                      }
                    ]
                  }
                }
              ]
            }
          }
        }
        :param lines:
        :return: string
        """
        payload = {
            'orderCancellation': {
                'orderLines': [{
                    'lineNumber': line['number'],
                    'orderLineStatuses': {
                        'orderLineStatus': [
                            {
                                'status': 'Cancelled',
                                'cancellationReason': 'CUSTOMER_REQUESTED_SELLER_TO_CANCEL',
                                'statusQuantity': {
                                    'unitOfMeasurement': 'EA',
                                    'amount': line['amount'],
                                }
                            }
                        ]
                    }
                } for line in lines]
            }
        }
        return dumps(payload)



    def ship(self, id, lines):
        url = self.url + '/%s/shipping' % id
        return self.connection.send_request(
            method='POST',
            url=url,
            body=self.get_ship_payload(lines)
        )

    def get_ship_payload(self, lines):
        """

        :param lines: list[ dict(number, amount, carrier, methodCode, trackingNumber, trackingUrl) ]
        :return:
        """
        """
        {
          "orderShipment": {
            "orderLines": {
              "orderLine": [
                {
                  "lineNumber": "1",
                  "orderLineStatuses": {
                    "orderLineStatus": [
                      {
                        "status": "Shipped",
                        "statusQuantity": {
                          "unitOfMeasurement": "EA",
                          "amount": "1"
                        },
                        "trackingInfo": {
                          "shipDateTime": 1488480443000,
                          "carrierName": {
                            "otherCarrier": null,
                            "carrier": "UPS"
                          },
                          "methodCode": "Express",
                          "trackingNumber": "12345",
                          "trackingURL": "www.fedex.com"
                        }
                      }
                    ]
                  }
                }
              ]
            }
          }
        }
        :param lines:
        :return:
        """

        payload = {
            "orderShipment": {
                "orderLines": {
                    "orderLine": [
                        {
                            "lineNumber": str(line['number']),
                            "orderLineStatuses": {
                                "orderLineStatus": [
                                    {
                                        "status": "Shipped",
                                        "statusQuantity": {
                                            "unitOfMeasurement": "EA",
                                            "amount": str(line['amount'])
                                        },
                                        "trackingInfo": {
                                            "shipDateTime": line['shipDateTime'],
                                            "carrierName": {
                                                "otherCarrier": None,
                                                "carrier": line['carrier']
                                            },
                                            "methodCode": line['methodCode'],
                                            "trackingNumber": line['trackingNumber'],
                                            "trackingURL": line['trackingUrl']
                                        }
                                    }
                                ]
                            }
                        }
                    for line in lines]
                }
            }
        }

        return dumps(payload)