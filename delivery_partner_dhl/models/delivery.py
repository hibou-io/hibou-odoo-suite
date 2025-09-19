import re

from odoo import fields, models, _
from odoo.exceptions import ValidationError


class PartnerShippingAccount(models.Model):
    _inherit = 'partner.shipping.account'
    
    delivery_type = fields.Selection(selection_add=[('dhl', 'DHL')], ondelete={'dhl': 'set default'})
    
    def dhl_check_validity(self):
        m = re.search(r'^(\d{8}|\d{9}|\d{10})$', self.name or '')
        if not m:
            raise ValidationError(_('DHL Account numbers must be 8-10 decimal numbers.'))
