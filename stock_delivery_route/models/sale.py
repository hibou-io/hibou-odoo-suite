from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    delivery_route_id = fields.Many2one('stock.warehouse.delivery.route', string='Delivery Route')

    @api.onchange('partner_id', 'partner_shipping_id', 'warehouse_id')
    def _prefill_delivery_route(self):
        for so in self:
            if so.warehouse_id:
                for route in so.partner_shipping_id.delivery_route_ids.filtered(lambda d: d.warehouse_id == so.warehouse_id):
                    so.delivery_route_id = route
                    break
                else:
                    for route in so.partner_id.delivery_route_ids.filtered(lambda d: d.warehouse_id == so.warehouse_id):
                        so.delivery_route_id = route
                        break
                    else:
                        so.delivery_route_id = False
            else:
                so.delivery_route_id = False

    def action_confirm(self):
        val = super(SaleOrder, self).action_confirm()
        for so in self:
            if so.delivery_route_id and so.picking_ids:
                so.picking_ids.write({'delivery_route_id': so.delivery_route_id.id})
        return val
