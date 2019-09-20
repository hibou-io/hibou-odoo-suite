from odoo import api, fields, models


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    catch_weight_ratio = fields.Float(string='Catch Weight Ratio', digits=(10, 6), compute='_compute_catch_weight_ratio')
    catch_weight = fields.Float(string='Catch Weight', digits=(10, 4))
    catch_weight_uom_id = fields.Many2one('uom.uom', related='product_id.catch_weight_uom_id')

    @api.depends('catch_weight')
    def _compute_catch_weight_ratio(self):
        for lot in self:
            if not lot.catch_weight_uom_id:
                lot.catch_weight_ratio = 1.0
            else:
                lot.catch_weight_ratio = lot.catch_weight_uom_id._compute_quantity(lot.catch_weight,
                                                                                   lot.product_id.uom_id,
                                                                                   rounding_method='DOWN')


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_catch_weight_uom_id = fields.Many2one('uom.uom', related="product_id.catch_weight_uom_id")

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super(StockMove, self)._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
        vals['catch_weight_uom_id'] = self.product_catch_weight_uom_id.id if self.product_catch_weight_uom_id else False
        return vals

    def action_show_details(self):
        action = super(StockMove, self).action_show_details()
        action['context']['show_catch_weight'] = bool(self.product_id.catch_weight_uom_id)
        return action


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    catch_weight_ratio = fields.Float(string='Catch Weight Ratio', digits=(10, 6), default=1.0)
    catch_weight = fields.Float(string='Catch Weight', digits=(10,4))
    catch_weight_uom_id = fields.Many2one('uom.uom', string='Catch Weight UOM')
    lot_catch_weight = fields.Float(related='lot_id.catch_weight')
    lot_catch_weight_uom_id = fields.Many2one('uom.uom', related='product_id.catch_weight_uom_id')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    has_catch_weight = fields.Boolean(string="Has Catch Weight", compute='_compute_has_catch_weight', store=True)

    @api.depends('move_lines.product_catch_weight_uom_id')
    def _compute_has_catch_weight(self):
        for picking in self:
            picking.has_catch_weight = any(picking.mapped('move_lines.product_catch_weight_uom_id'))


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    lot_catch_weight_ratio = fields.Float(related='lot_id.catch_weight_ratio')
    lot_catch_weight = fields.Float(related='lot_id.catch_weight')
    lot_catch_weight_uom_id = fields.Many2one('uom.uom', related='lot_id.catch_weight_uom_id')
