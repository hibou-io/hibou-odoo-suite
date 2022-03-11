# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    shipping_calendar_id = fields.Many2one(
        'resource.calendar', 'Shipping Calendar',
        help="This calendar represents shipping availability from the warehouse.")
    sale_planner_carrier_ids = fields.Many2many('delivery.carrier',
                                                relation='sale_planner_carrier_wh_rel',
                                                string='Sale Order Planner Base Carriers',
                                                help='Overrides the global carriers.')
