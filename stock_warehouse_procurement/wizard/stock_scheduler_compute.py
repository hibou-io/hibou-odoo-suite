from odoo import api, fields, models


class StockSchedulerCompute(models.TransientModel):
    _inherit = 'stock.scheduler.compute'

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')

    @api.multi
    def procure_calculation(self):
        self.ensure_one()
        if self.warehouse_id:
            self = self.with_context(warehouse_id=self.warehouse_id.id)
        return super(StockSchedulerCompute, self).procure_calculation()
