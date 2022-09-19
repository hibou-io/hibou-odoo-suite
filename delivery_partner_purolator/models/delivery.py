from odoo import fields, models


class PartnerShippingAccount(models.Model):
    _inherit = 'partner.shipping.account'
    
    delivery_type = fields.Selection(selection_add=[('purolator', 'Purolator')], ondelete={'purolator': 'set default'})
