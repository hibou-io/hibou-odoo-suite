from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class AddProductionItem(models.TransientModel):
    _name = 'wiz.add.production.item'
    _description = 'Add Production Item'

    @api.model
    def _default_production_id(self):
        return self.env.context.get('active_id', False)

    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_qty = fields.Float(
        'Product Quantity', digits=dp.get_precision('Product Unit of Measure'),
        required=True,
        default=1.0)
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    production_id = fields.Many2one(
        'mrp.production', 'Production Order',
        default=_default_production_id)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for item in self:
            if item.product_id:
                item.product_uom_id = item.product_id.uom_id
            else:
                item.product_uom_id = False

    def add_item(self):
        for item in self:
            if item.product_qty <= 0:
                raise UserError('Please provide a positive quantity to add')

            bom_line = self.env['mrp.bom.line'].new({
                'product_id': item.product_id.id,
                'product_qty': item.product_qty,
                'bom_id': item.production_id.bom_id.id,
                'product_uom_id': item.product_uom_id.id,
            })

            move = item.production_id._get_move_raw_values(bom_line, {
                'qty': item.product_qty,
                'product': item.product_id,
                'original_qty': item.product_qty,
                'parent_line': None})
            move = self.env['stock.move'].create(move)
            move.write({
                'group_id': item.production_id.procurement_group_id.id,
                'unit_factor': move.product_uom_qty / item.production_id.product_qty,
                'reference': item.production_id.name,
            })
            move._action_confirm()

        return True
