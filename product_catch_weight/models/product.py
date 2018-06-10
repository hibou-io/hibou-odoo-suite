from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.template'

    catch_weight_uom_id = fields.Many2one('product.uom', string='Catch Weight UOM')
