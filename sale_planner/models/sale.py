# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_planorder(self):
        plan_obj = self.env['sale.order.make.plan']
        for order in self:
            plan = plan_obj.create({
                'order_id': order.id,
            })
            action = self.env.ref('sale_planner.action_plan_sale_order').read()[0]
            action['res_id'] = plan.id
            return action
