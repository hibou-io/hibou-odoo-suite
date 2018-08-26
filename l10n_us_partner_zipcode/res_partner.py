# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)

try:
    from uszipcode import ZipcodeSearchEngine
except ImportError:
    _logger.warn('module "uszipcode" cannot be loaded, you will be unable to detect Cities and States by ZIP')
    ZipcodeSearchEngine = None

from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.onchange('zip')
    def _zip_to_city_state(self):
        if ZipcodeSearchEngine and self.zip and not self.city:
            country_us = self.env['res.country'].search([('code', '=', 'US')], limit=1)
            state_obj = self.env['res.country.state']
            if not self.country_id or self.country_id.id == country_us.id:
                with ZipcodeSearchEngine() as search:
                    zipcode = search.by_zipcode(self.zip)
                    if zipcode:
                        if not self.country_id:
                            self.country_id = country_us

                        self.city = zipcode['City']
                        self.state_id = state_obj.search([
                            ('code', '=', zipcode['State']),
                            ('country_id', '=', country_us.id),
                        ], limit=1)

                        if hasattr(self, 'partner_latitude') and not self.partner_latitude:
                            self.partner_latitude = zipcode['Latitude']
                            self.partner_longitude = zipcode['Longitude']
                            self.date_localization = fields.Date.context_today(self)
        return {}
