from odoo import api, fields, models


class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    shipping_calendar_id = fields.Many2one(
        'resource.calendar', 'Shipping Calendar',
        help="This calendar represents shipping availability from the warehouse.")
