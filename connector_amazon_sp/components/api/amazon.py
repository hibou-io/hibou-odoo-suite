# © 2021 Hibou Corp.

# imports for Client and CredentialProvider patch
from os import environ
import json
from requests import request
import boto3
from botocore.config import Config as BotoConfig

from sp_api.base.client import Client
from sp_api.base.config import CredentialProvider
from sp_api.base.ApiResponse import ApiResponse
from sp_api.base.marketplaces import Marketplaces
from sp_api.auth import AccessTokenClient
from requests.exceptions import HTTPError

# imports for Wrapping
from sp_api.api import Orders, \
                       Shipping, \
                       MerchantFulfillment, \
                       Feeds

from sp_api.base.exceptions import SellingApiException, \
                                   SellingApiForbiddenException

amz_proxy_endpoint = environ.get('AMAZON_SP_ENDPOINT', 'https://amz-proxy.hibou.io')

PROXY_ENDPOINT = amz_proxy_endpoint
PROXY = amz_proxy_endpoint.split('//')[1]


class RequestRateError(Exception):
    def __init__(self, message, exception=None):
        super().__init__(message)
        self.exception = exception


class WrappedAPI:
    SellingApiException = SellingApiException
    SellingApiForbiddenException = SellingApiForbiddenException

    def __init__(self, env, refresh_token, lwa_client_id, lwa_client_secret, aws_access_key, aws_secret_key, role_arn):
        self.env = env
        get_param = env['ir.config_parameter'].sudo().get_param
        self.credentials = {
            'refresh_token': refresh_token,
            'lwa_app_id': lwa_client_id,
            'lwa_client_secret': lwa_client_secret,
            'aws_access_key': aws_access_key,
            'aws_secret_key': aws_secret_key,
            'role_arn': role_arn,
            # 'db_uid': get_param('database.uuid', ''),
            # 'pro_code': get_param('database.hibou_professional_code', ''),
        }

    def orders(self):
        return Orders(credentials=self.credentials)

    def shipping(self):
        return Shipping(credentials=self.credentials)

    def merchant_fulfillment(self):
        return MerchantFulfillment(credentials=self.credentials)

    def feeds(self):
        return Feeds(credentials=self.credentials)


# patch the Client
def __init__(
        self,
        marketplace: Marketplaces = Marketplaces.US,
        *,
        refresh_token=None,
        account='default',
        credentials=None
):
    super(Client, self).__init__(account, credentials)
    self.boto3_client = boto3.client(
        'sts',
        # aws_access_key_id=self.credentials.aws_access_key,
        # aws_secret_access_key=self.credentials.aws_secret_key
        config=BotoConfig(proxies={'http': PROXY, 'https': PROXY})
    )
    self.endpoint = marketplace.endpoint
    self.marketplace_id = marketplace.marketplace_id
    self.region = marketplace.region
    self._auth = AccessTokenClient(refresh_token=refresh_token, account=account, credentials=credentials)


def _sign_request(self):
    return None


def _request(self, path: str, *, data: dict = None, params: dict = None, headers=None,
             add_marketplace=True) -> ApiResponse:
    if params is None:
        params = {}
    if data is None:
        data = {}

    self.method = params.pop('method', data.pop('method', 'GET'))

    if add_marketplace:
        self._add_marketplaces(data if self.method in ('POST', 'PUT') else params)

    # auth=None because we don't sign the request anymore
    # proxy setup...
    # url = self.endpoint + path
    url = PROXY_ENDPOINT + path
    headers = headers or self.headers
    headers['x-orig-host'] = headers['host']
    del headers['host']
    headers['x-db-uuid'] = self.credentials.db_uid
    headers['x-pro-code'] = self.credentials.pro_code
    res = request(self.method, url, params=params,
                  data=json.dumps(data) if data and self.method in ('POST', 'PUT') else None, headers=headers,
                  auth=self._sign_request())
    try:
        res.raise_for_status()  # proxy does not return json errors
    except HTTPError as e:
        status_code = e.response.status_code
        if str(status_code) == '429':
            raise RequestRateError('HTTP 429', exception=e)
        raise e
    return self._check_response(res)

# Patch _request to have timeout, not signing differences above.
def _request(self, path: str, *, data: dict = None, params: dict = None, headers=None,
             add_marketplace=True) -> ApiResponse:
    if params is None:
        params = {}
    if data is None:
        data = {}

    self.method = params.pop('method', data.pop('method', 'GET'))

    if add_marketplace:
        self._add_marketplaces(data if self.method in ('POST', 'PUT') else params)

    res = request(self.method, self.endpoint + path, params=params,
                  data=json.dumps(data) if data and self.method in ('POST', 'PUT') else None, headers=headers or self.headers,
                  auth=self._sign_request(),
                  timeout=60)

    return self._check_response(res)

# Client.__init__ = __init__
# Client._sign_request = _sign_request
Client._request = _request


# patch the CredentialProvider
class Config:
    def __init__(self,
                 refresh_token,
                 lwa_app_id,
                 lwa_client_secret,
                 aws_access_key,
                 aws_secret_key,
                 role_arn,
                 db_uid,
                 pro_code,
                 ):
        self.refresh_token = refresh_token
        self.lwa_app_id = lwa_app_id
        self.lwa_client_secret = lwa_client_secret
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        self.role_arn = role_arn
        self.db_uid = db_uid
        self.pro_code = pro_code

    def check_config(self):
        errors = []
        for k, v in self.__dict__.items():
            if not v and k != 'refresh_token':
                errors.append(k)
        return errors


# CredentialProvider.Config = Config
