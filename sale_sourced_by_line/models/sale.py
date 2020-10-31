from collections import defaultdict
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    date_planned = fields.Datetime('Planned Date')
    requested_date = fields.Datetime('Requested Date')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # In 13, this field exists, but isn't stored and is computed during
    # computation for available inventory (set to order's warehouse)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',
                                   compute=None, store=True)
    date_planned = fields.Datetime('Planned Date')

    def _prepare_procurement_values(self, group_id=False):
        vals = super(SaleOrderLine, self)._prepare_procurement_values(group_id=group_id)
        if self.warehouse_id:
            vals.update({'warehouse_id': self.warehouse_id})
        if self.date_planned:
            vals.update({'date_planned': self.date_planned})
        elif self.order_id.date_planned:
            vals.update({'date_planned': self.order_id.date_planned})
        return vals

    # Needs modifications to not actually set a warehouse on the line as it is now stored
    @api.depends('product_id', 'customer_lead', 'product_uom_qty', 'product_uom', 'order_id.warehouse_id', 'order_id.commitment_date')
    def _compute_qty_at_date(self):
        """ Compute the quantity forecasted of product at delivery date. There are
        two cases:
         1. The quotation has a commitment_date, we take it as delivery date
         2. The quotation hasn't commitment_date, we compute the estimated delivery
            date based on lead time"""
        qty_processed_per_product = defaultdict(lambda: 0)
        grouped_lines = defaultdict(lambda: self.env['sale.order.line'])
        # We first loop over the SO lines to group them by warehouse and schedule
        # date in order to batch the read of the quantities computed field.
        for line in self:
            if not (line.product_id and line.display_qty_widget):
                continue
            # use warehouse from line or order
            warehouse = line.warehouse_id or line.order_id.warehouse_id
            # line.warehouse_id = line.order_id.warehouse_id
            if line.order_id.commitment_date:
                date = line.order_id.commitment_date
            else:
                date = line._expected_date()
            grouped_lines[(warehouse.id, date)] |= line

        treated = self.browse()
        for (warehouse, scheduled_date), lines in grouped_lines.items():
            product_qties = lines.mapped('product_id').with_context(to_date=scheduled_date, warehouse=warehouse).read([
                'qty_available',
                'free_qty',
                'virtual_available',
            ])
            qties_per_product = {
                product['id']: (product['qty_available'], product['free_qty'], product['virtual_available'])
                for product in product_qties
            }
            for line in lines:
                line.scheduled_date = scheduled_date
                qty_available_today, free_qty_today, virtual_available_at_date = qties_per_product[line.product_id.id]
                line.qty_available_today = qty_available_today - qty_processed_per_product[line.product_id.id]
                line.free_qty_today = free_qty_today - qty_processed_per_product[line.product_id.id]
                line.virtual_available_at_date = virtual_available_at_date - qty_processed_per_product[line.product_id.id]
                if line.product_uom and line.product_id.uom_id and line.product_uom != line.product_id.uom_id:
                    line.qty_available_today = line.product_id.uom_id._compute_quantity(line.qty_available_today, line.product_uom)
                    line.free_qty_today = line.product_id.uom_id._compute_quantity(line.free_qty_today, line.product_uom)
                    line.virtual_available_at_date = line.product_id.uom_id._compute_quantity(line.virtual_available_at_date, line.product_uom)
                qty_processed_per_product[line.product_id.id] += line.product_uom_qty
            treated |= lines
        remaining = (self - treated)
        remaining.virtual_available_at_date = False
        remaining.scheduled_date = False
        remaining.free_qty_today = False
        remaining.qty_available_today = False
        # don't unset warehouse as it may be set by hand
        # remaining.warehouse_id = False
