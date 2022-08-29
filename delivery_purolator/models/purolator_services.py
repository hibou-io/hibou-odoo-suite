from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep.cache import SqliteCache
from zeep.transports import Transport
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class PurolatorClient(object):
    def __init__(self, carrier):
        if carrier.delivery_type != 'purolator':
            raise UserError('Invalid carrier: %s' % carrier.name)
        self.api_key = carrier.purolator_api_key
        self.password = carrier.purolator_password
        self.activation_key = carrier.purolator_activation_key
        self.account_number = carrier.purolator_account_number
        self.service_type = carrier.purolator_service_type
        self._wsdl_base = "https://devwebservices.purolator.com"
        if carrier.prod_environment:
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
        # _logger.warning('*** header_value:\n%s' % header_value)
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
        :returns: dict
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
        # _logger.warning('**** GetQuickEstimate response:\n%s', response)
        errors = response['body']['ResponseInformation']['Errors']
        if errors:
            return {
                'price': 0.0,
                'error': '\n'.join(['%s: %s' % (error['Code'], error['Description']) for error in errors['Error']]),
            }
        shipments = response['body']['ShipmentEstimates']['ShipmentEstimate']
        shipment = list(filter(lambda s: s['ServiceID'] == self.service_type, shipments))
        if shipment:
            return {
                'price': shipment[0]['TotalPrice'],
                'error': False,
            }
        return {
            'price': 0.0,
            'error': 'Purolator ServiceID not found',
        }
