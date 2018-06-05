from odoo import api, fields, models


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    catch_weight_ratio = fields.Float(string='Catch Weight Ratio', digits=(10, 6), default=1.0)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    lot_catch_weight_ratio = fields.Float(string='Catch Weight Ratio', digits=(10, 6), default=1.0)
    lot_catch_weight_ratio_related = fields.Float(related='lot_id.catch_weight_ratio')
    #lot_catch_weight_ratio = fields.Float(related='lot_id.catch_weight_ratio')

    # def _action_done(self):
    #     super(StockMoveLine, self)._action_done()
    #     for ml in self.filtered(lambda l: l.product_id.tracking == 'serial' and l.lot_id):
    #         ml.lot_id.catch_weight_ratio = ml.lot_catch_weight_ratio
