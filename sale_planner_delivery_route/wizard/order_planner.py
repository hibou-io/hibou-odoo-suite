from odoo import api, fields, models
from odoo.addons.sale_planner.wizard.order_planner import distance


class SaleOrderMakePlan(models.TransientModel):
    _inherit = 'sale.order.make.plan'

    def generate_base_option(self, order_fake):
        option = super(SaleOrderMakePlan, self).generate_base_option(order_fake)
        option['delivery_route_id'] = self.find_closest_route(option, order_fake)
        return option

    def find_closest_route(self, option, order_fake):
        warehouse = self.env['stock.warehouse'].browse(option['warehouse_id'])
        if warehouse.delivery_route_ids:
            partner = order_fake.partner_shipping_id
            if not partner.date_localization:
                partner.geo_localize()
            return self._find_closest_route_id(warehouse.delivery_route_ids,
                                            partner.partner_latitude,
                                            partner.partner_longitude)
        return False

    def _find_closest_route_id(self, routes, latitude, longitude):
        distances = {distance(latitude, longitude, route.latitude, route.longitude): route.id for route in routes}
        route_id = distances[min(distances)]
        return route_id

    def _order_fields_for_option(self, option):
        vals = super(SaleOrderMakePlan, self)._order_fields_for_option(option)
        vals['delivery_route_id'] = option.delivery_route_id.id
        return vals


class SaleOrderPlanningOption(models.TransientModel):
    _inherit = 'sale.order.planning.option'

    delivery_route_id = fields.Many2one('stock.warehouse.delivery.route', string='Delivery Route')
