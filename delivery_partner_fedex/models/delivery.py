import re

from odoo import fields, models
from odoo.exceptions import ValidationError


class PartnerShippingAccount(models.Model):
    _inherit = 'partner.shipping.account'

    delivery_type = fields.Selection(selection_add=[('fedex', 'FedEx')])

    def fedex_check_validity(self):
        m = re.search(r'^\d{9}$', self.name or '')
        if not m:
            raise ValidationError('FedEx Account numbers must be 9 decimal numbers.')


