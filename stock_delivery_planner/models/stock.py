from odoo import fields, models, tools, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_plan_delivery(self):
        context = dict(self.env.context or {})
        planner_model = self.env['stock.delivery.planner']
        for picking in self:
            planner = planner_model.create({
                'picking_id': picking.id,
            })
            return {
                'name': _('Plan Delivery'),
                'type': 'ir.actions.act_window',
                'res_model': 'stock.delivery.planner',
                'res_id': planner.id,
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('stock_delivery_planner.view_stock_delivery_planner').id,
                'target': 'new',
                'context': context,
            }

    # def get_shipping_carriers(self, carrier_id=None, domain=None):
    def get_shipping_carriers(self):
        Carrier = self.env['delivery.carrier'].sudo()
        # if carrier_id:
        #     return Carrier.browse(carrier_id)
        #
        # if domain:
        #     if not isinstance(domain, (list, tuple)):
        #         domain = tools.safe_eval(domain)
        # else:
        domain = []

        if self.env.context.get('carrier_domain'):
            # potential bug here if this is textual
            domain.extend(self.env.context.get('carrier_domain'))

        irconfig_parameter = self.env['ir.config_parameter'].sudo()
        if irconfig_parameter.get_param('sale.order.planner.carrier_domain'):
            domain.extend(tools.safe_eval(irconfig_parameter.get_param('sale.order.planner.carrier_domain')))

        return Carrier.search(domain)
