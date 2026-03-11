from collections import defaultdict
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    date_planned = fields.Datetime('Planned Date')
    requested_date = fields.Datetime('Requested Date')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # In 14, this field exists, but isn't stored and is merely related to the
    # order's warehouse_id, it is only used in computation of availability
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',
                                   compute=None, related=None, store=True)
    date_planned = fields.Datetime('Planned Date')

    def _prepare_procurement_values(self, group_id=False):
        vals = super(SaleOrderLine, self)._prepare_procurement_values(group_id=group_id)
        vals.update({'warehouse_id': self.warehouse_id or self.order_id.warehouse_id})
        if self.date_planned:
            vals.update({'date_planned': self.date_planned})
        elif self.order_id.date_planned:
            vals.update({'date_planned': self.order_id.date_planned})
        return vals
