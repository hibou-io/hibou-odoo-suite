from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_commission_exempt = fields.Boolean('Exclude from Commissions')
