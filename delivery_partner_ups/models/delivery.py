import re

from odoo import fields, models
from odoo.exceptions import ValidationError


class PartnerShippingAccount(models.Model):
    _inherit = 'partner.shipping.account'

    delivery_type = fields.Selection(selection_add=[('ups', 'UPS')])
    ups_zip = fields.Char(string='UPS Account ZIP')

    def ups_check_validity(self):
        m = re.search(r'^[\dA-Z]{6}$', self.name or '')
        if not m:
            raise ValidationError('UPS Account numbers must be 6 Alpha-numeric characters.')
        m = re.search(r'^\d{5}$', self.ups_zip or '')
        if not m:
            raise ValidationError('UPS requires the 5 digit account ZIP.')
