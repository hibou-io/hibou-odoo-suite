from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    date_planned = fields.Datetime('Planned Date')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    date_planned = fields.Datetime('Planned Date')

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        vals = super(SaleOrderLine, self)._prepare_procurement_values(group_id=group_id)
        if self.warehouse_id:
            vals.update({'warehouse_id': self.warehouse_id})
        if self.date_planned:
            vals.update({'date_planned': self.date_planned})
        elif self.order_id.date_planned:
            vals.update({'date_planned': self.order_id.date_planned})
        return vals
