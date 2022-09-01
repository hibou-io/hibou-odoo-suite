from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep.cache import SqliteCache
from zeep.transports import Transport
from odoo.exceptions import UserError


class PurolatorClient(object):
    def __init__(self, api_key, password, activation_key, account_number, is_prod):
        self.api_key = api_key
        self.password = password
        self.activation_key = activation_key
        self.account_number = account_number
        self._wsdl_base = "https://devwebservices.purolator.com"
        if is_prod:
            self._wsdl_base = "https://webservices.purolator.com"
            
        session = Session()
        session.auth = HTTPBasicAuth(self.api_key, self.password)
        self.transport = Transport(cache=SqliteCache(), session=session)
        
    def _get_client(self, wsdl_path):
        client = Client(self._wsdl_base + wsdl_path,
                        transport=self.transport)
        request_context = client.get_element('ns1:RequestContext')
        header_value = request_context(
            Version='2.0',
            Language='en',
            GroupID='xxx',
            RequestReference='RatingExample',
            UserToken=self.activation_key,
        )
        client.set_default_soapheaders([header_value])
        return client
            
    def get_quick_estimate(self, sender_postal_code, receiver_address, package_type, total_weight):
        """ Call GetQuickEstimate
        
        :param sender_postal_code: string
        :param receiver_address: dict {'City': string,
                                       'Province': string,
                                       'Country': string,
                                       'PostalCode': string}
        :param package_type: string
        :param total_weight: float (in pounds)
        :returns: dict {'shipments': list, 'error': string or False}
        """
        client = self._get_client('/EWS/V2/Estimating/EstimatingService.asmx?wsdl')
        response = client.service.GetQuickEstimate(
            BillingAccountNumber=self.account_number,
            SenderPostalCode=sender_postal_code,
            ReceiverAddress=receiver_address,
            PackageType=package_type,
            TotalWeight={
                'Value': 10.0,
                'WeightUnit': 'lb',
                },
            )
        errors = response['body']['ResponseInformation']['Errors']
        if errors:
            return {
                'shipments': False,
                'error': '\n'.join(['%s: %s' % (error['Code'], error['Description']) for error in errors['Error']]),
            }
        shipments = response['body']['ShipmentEstimates']['ShipmentEstimate']
        if shipments:
            return {
                'shipments': shipments,
                'error': False,
            }
        return {
            'shipments': False,
            'error': 'Purolator service did not return any matching rates.',
        }
