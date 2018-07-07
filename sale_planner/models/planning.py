from odoo import api, fields, models


class PlanningPolicy(models.Model):
    _name = 'sale.order.planning.policy'

    name = fields.Char(string='Name')
    carrier_filter_id = fields.Many2one(
        'ir.filters',
        string='Delivery Carrier Filter',
    )
    warehouse_filter_id = fields.Many2one(
        'ir.filters',
        string='Warehouse Filter',
    )
    always_closest_warehouse = fields.Boolean(string='Always Plan Closest Warehouse')
