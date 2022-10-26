from odoo import api, fields, models


class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    delivery_route_ids = fields.One2many('stock.warehouse.delivery.route', 'warehouse_id', string='Delivery Routes')


class Picking(models.Model):
    _inherit = 'stock.picking'
    _order = 'sequence asc, priority desc, date asc, id desc'

    sequence = fields.Integer(string='Sequence')
    warehouse_id = fields.Many2one('stock.warehouse', related='picking_type_id.warehouse_id')
    delivery_route_id = fields.Many2one('stock.warehouse.delivery.route', string='Delivery Route')
    partner_address = fields.Char(string='Address', compute='_compute_partner_address')

    def _compute_partner_address(self):
        for pick in self:
            if pick.partner_id:
                pick.partner_address = '%s: %s, %s' % (pick.partner_id.name or '', pick.partner_id.street or '', pick.partner_id.city or '')
            else:
                pick.partner_address = ''


class WarehouseDeliveryRoute(models.Model):
    _name = 'stock.warehouse.delivery.route'

    name = fields.Char(string='Name')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    note = fields.Text(string='Note')

    def name_get(self):
        res = []
        for route in self:
            res.append((route.id, '[%s] %s' % (route.warehouse_id.code, route.name)))
        return res



