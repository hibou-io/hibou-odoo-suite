from odoo import fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    delivery_route_ids = fields.Many2many('stock.warehouse.delivery.route', string="Delivery Routes")
