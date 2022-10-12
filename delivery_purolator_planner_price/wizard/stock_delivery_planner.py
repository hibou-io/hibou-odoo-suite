# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import models


class StockDeliveryPlanner(models.TransientModel):
    _inherit = 'stock.delivery.planner'
    
    def action_plan(self):
        res = super().action_plan()
        puro_package_options = self.plan_option_ids.filtered(
            lambda o: (o.package_id 
                       and o.selection == 'selected'
                       and o.carrier_id.delivery_type == 'purolator'
        ))
        if puro_package_options:
            self.picking_id.carrier_price = sum(puro_package_options.mapped('price'))
        return res
