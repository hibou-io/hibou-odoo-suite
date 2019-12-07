import os
import logging
from suds.client import Client

_logger = logging.getLogger(__name__)


class CATaxRequest:
    def __init__(self):
        wsdl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), './ca_rates.wsdl')
        self.client = Client('file:///%s' % wsdl_path.lstrip('/'))

    def get_rate(self, partner):
        request = self.client.factory.create('CARateRequest')
        request.StreetAddress = partner.street
        request.State = partner.state_id.code
        request.City = partner.city
        zip_ = partner.zip
        if zip_ and len(zip_) > 5:
            zip_ = zip_[:5]
        request.ZipCode = zip_

        _logger.debug('CA Request: ' + str(request))
        response = self.client.service.GetRate(request)
        _logger.debug('CA Response: ' + str(response))
        return {
            'rate': response.CARateResponses[0][0].Responses[0][0].Rate * 100.0,
            'county': response.CARateResponses[0][0].Responses[0][0].Details.County,
        }
