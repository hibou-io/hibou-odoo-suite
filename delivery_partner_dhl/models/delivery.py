import re

from odoo import fields, models
from odoo.exceptions import ValidationError


class PartnerShippingAccount(models.Model):
    _inherit = 'partner.shipping.account'

    delivery_type = fields.Selection(selection_add=[('dhl', 'DHL')])

    def dhl_check_validity(self):
        m = re.search('^\d{10}$', self.name or '')
        if not m:
            raise ValidationError('DHL Account numbers must be 10 decimal numbers.')


