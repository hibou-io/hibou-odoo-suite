from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SaleLineChangeOrder(models.TransientModel):
    _name = 'sale.line.change.order'
    _description = 'Sale Line Change Order'

    order_id = fields.Many2one('sale.order', string='Sale Order')
    line_ids = fields.One2many('sale.line.change.order.line', 'change_order_id', string='Change Lines')

    @api.model
    def default_get(self, fields):
        rec = super(SaleLineChangeOrder, self).default_get(fields)
        if 'order_id' in rec:
            order = self.env['sale.order'].browse(rec['order_id'])
            if not order:
                return rec

            line_model = self.env['sale.line.change.order.line']
            rec['line_ids'] = [(0, 0, line_model.values_from_so_line(l)) for l in order.order_line]
        return rec

    def apply(self):
        self.ensure_one()
        self.line_ids.apply()
        return True


class SaleLineChangeOrderLine(models.TransientModel):
    _name = 'sale.line.change.order.line'

    change_order_id = fields.Many2one('sale.line.change.order')
    sale_line_id = fields.Many2one('sale.order.line', string='Sale Line')
    line_ordered_qty = fields.Float(string='Ordered Qty')
    line_delivered_qty = fields.Float(string='Delivered Qty')
    line_reserved_qty = fields.Float(string='Reserved Qty')
    line_date_planned = fields.Datetime(string='Planned Date')
    line_warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    line_route_id = fields.Many2one('stock.location.route', string='Route')

    def values_from_so_line(self, so_line):
        move_ids = so_line.move_ids
        reserved_qty = sum(move_ids.mapped('reserved_availability'))
        return {
            'sale_line_id': so_line.id,
            'line_ordered_qty': so_line.product_uom_qty,
            'line_delivered_qty': so_line.qty_delivered,
            'line_reserved_qty': reserved_qty,
            'line_date_planned': so_line.date_planned,
            'line_warehouse_id': so_line.warehouse_id.id,
            'line_route_id': so_line.route_id.id,
        }

    def _apply(self):
        self._apply_clean_dropship()
        self._apply_clean_existing_moves()
        self._apply_new_values()
        self._apply_procurement()

    def _apply_clean_dropship(self):
        po_line_model = self.env['purchase.order.line'].sudo()
        po_lines = po_line_model.search([('sale_line_id', 'in', self.mapped('sale_line_id.id'))])

        if po_lines and po_lines.filtered(lambda l: l.order_id.state != 'cancel'):
            names = ', '.join(po_lines.filtered(lambda l: l.order_id.state != 'cancel').mapped('order_id.name'))
            raise ValidationError('One or more lines has existing non-cancelled Purchase Orders associated: ' + names)

    def _apply_clean_existing_moves(self):
        moves = self.mapped('sale_line_id.move_ids').filtered(lambda m: m.state != 'done')
        moves._action_cancel()

    def _apply_new_values(self):
        for line in self:
            line.sale_line_id.write({
                'date_planned': line.line_date_planned,
                'warehouse_id': line.line_warehouse_id.id,
                'route_id': line.line_route_id.id,
            })

    def _apply_procurement(self):
        self.mapped('sale_line_id')._action_launch_stock_rule()

    def apply(self):
        changed_lines = self.filtered(lambda l: (
                l.sale_line_id.warehouse_id != l.line_warehouse_id
                or l.sale_line_id.route_id != l.line_route_id))
        changed_lines._apply()
