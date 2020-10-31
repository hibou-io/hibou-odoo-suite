from odoo import api, fields, models

try:
    from uszipcode import SearchEngine
except ImportError:
    SearchEngine = None


class Partner(models.Model):
    _inherit = 'res.partner'

    def geo_localize(self):
        # We need country names in English below
        for partner in self.with_context(lang='en_US'):
            try:
                if SearchEngine and partner.zip:
                    with SearchEngine() as search:
                        zipcode = search.by_zipcode(str(self.zip).split('-')[0])
                        if zipcode and zipcode.lat:
                            partner.write({
                                'partner_latitude': zipcode.lat,
                                'partner_longitude': zipcode.lng,
                                'date_localization': fields.Date.context_today(partner),
                            })
                        else:
                            super(Partner, partner).geo_localize()
                else:
                    super(Partner, partner).geo_localize()
            except:
                pass
        return True
