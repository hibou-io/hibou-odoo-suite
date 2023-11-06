import re

from odoo import fields, models, _
from odoo.exceptions import ValidationError


class PartnerShippingAccount(models.Model):
    _inherit = 'partner.shipping.account'
    
    delivery_type = fields.Selection(selection_add=[('fedex', 'FedEx')], ondelete={'fedex': 'set default'})
    
    def fedex_check_validity(self):
        m = re.search(r'^\d{9}$', self.name or '')
        if not m:
            raise ValidationError(_('FedEx Account numbers must be 9 decimal numbers.'))
