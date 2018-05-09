from odoo import fields, models


class DeliveryRoute(models.Model):
    _inherit = 'stock.warehouse.delivery.route'

    latitude = fields.Float(string='Latitude', digits=(12, 6))
    longitude = fields.Float(string='Longitude', digits=(12, 6))
