# -*- coding: utf-8 -*-
from urllib2 import urlopen, quote, HTTPError
from ssl import _create_unverified_context
from logging import getLogger

from odoo.exceptions import ValidationError

_logger = getLogger(__name__)


class WATaxRequest(object):
    def __init__(self):
        pass

    def get_rate(self, partner):
        # https://webgis.dor.wa.gov/webapi/addressrates.aspx/?output=text\&addr=test\&city=Marysville\&zip=98270
        if not all((partner.street, partner.city, partner.zip)):
            raise ValidationError('WATaxRequest impossible without Street, City and ZIP.')
        url = 'https://webgis.dor.wa.gov/webapi/addressrates.aspx?output=text&addr=' + quote(partner.street) + \
            '&city=' + quote(partner.city) + '&zip=' + quote(partner.zip)
        _logger.info(url)
        try:
            response = urlopen(url, context=_create_unverified_context())
            response_body = response.read()
            _logger.info(response_body)
        except HTTPError as e:
            _logger.warn('Error on request: ' + str(e))
            response_body = ''

        return self._parse_rate(response_body)

    def is_success(self, result):
        '''
            ADDRESS = 0,
            LATLON = 0,
            PLUS4 = 1,
            ADDRESS_STANARDIZED = 2,
            PLUS4_STANARDIZED = 3,
            ADDRESS_CHANGED = 4,
            ZIPCODE = 5,
            ADDRESS_NOT_FOUND = 6,
            LATLON_NOT_FOUND = 7,
            POI = 8,
            ERROR = 9
            internal parse_error = 100
        '''
        if 'result_code' not in result or result['result_code'] >= 9 or result['result_code'] < 0:
            return False
        return True

    def _parse_rate(self, response_body):
        # 'LocationCode=1704 Rate=0.100 ResultCode=0'
        # {
        #   'result_code': 0,
        #   'location_code': '1704',
        #   'rate': '10.00',
        # }

        res = {'result_code': 100}
        if len(response_body) > 200:
            # this likely means that they returned an HTML page
            return res

        body_parts = response_body.split(' ')
        for part in body_parts:
            if part.find('ResultCode=') >= 0:
                res['result_code'] = int(part[len('ResultCode='):])
            elif part.find('Rate=') >= 0:
                res['rate'] = '%.2f' % (float(part[len('Rate='):]) * 100.0)
            elif part.find('LocationCode=') >= 0:
                res['location_code'] = part[len('LocationCode='):]
            elif part.find('debughint=') >= 0:
                res['debug_hint'] = part[len('debughint='):]
        return res
