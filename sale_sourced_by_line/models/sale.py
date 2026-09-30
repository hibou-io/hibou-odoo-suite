from collections import defaultdict
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    date_planned = fields.Datetime('Planned Date')
    requested_date = fields.Datetime('Requested Date')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    date_planned = fields.Datetime('Planned Date')

    @api.depends('route_ids', 'order_id.warehouse_id', 'product_id')
    def _compute_warehouse_id(self):
        """
        OVERRIDE: compute the warehouse for the lines only
        if it has not already been set."""
        lines = self.filtered(lambda rec: not rec.warehouse_id)
        return super(SaleOrderLine, lines)._compute_warehouse_id()

    def _prepare_procurement_values(self):
        vals = super(SaleOrderLine, self)._prepare_procurement_values()
        vals.update({'warehouse_id': self.warehouse_id or self.order_id.warehouse_id})
        if self.date_planned:
            vals.update({'date_planned': self.date_planned})
        elif self.order_id.date_planned:
            vals.update({'date_planned': self.order_id.date_planned})
        return vals
