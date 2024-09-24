from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    is_digital = fields.Boolean(help='Used in Signifyd case creation.')
    # TODO add to view