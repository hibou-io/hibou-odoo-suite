from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    no_commission = fields.Boolean('Exclude from Commissions')
