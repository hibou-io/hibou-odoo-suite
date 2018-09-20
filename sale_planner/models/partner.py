from odoo import api, fields, models

try:
    from uszipcode import ZipcodeSearchEngine
except ImportError:
    ZipcodeSearchEngine = None


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def geo_localize(self):
        # We need country names in English below
        for partner in self.with_context(lang='en_US'):
            if ZipcodeSearchEngine and partner.zip:
                with ZipcodeSearchEngine() as search:
                    zipcode = search.by_zipcode(partner.zip)
                    if zipcode:
                        partner.write({
                            'partner_latitude': zipcode['Latitude'],
                            'partner_longitude': zipcode['Longitude'],
                            'date_localization': fields.Date.context_today(partner),
                        })
                    else:
                        super(Partner, partner).geo_localize()
            else:
                super(Partner, partner).geo_localize()
        return True
