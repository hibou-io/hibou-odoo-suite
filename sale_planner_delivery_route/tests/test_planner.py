from odoo.addons.sale_planner.tests.test_planner import TestPlanner


class TestPlannerRoute(TestPlanner):
    def setUp(self):
        super(TestPlannerRoute, self).setUp()
        self.route_near = self.env['stock.warehouse.delivery.route'].create({
            'name': 'Route 1',
            'warehouse_id': self.warehouse_1.id,
            'latitude': 48.02995,
            'longitude': -122.14771,
        })
        self.route_far = self.env['stock.warehouse.delivery.route'].create({
            'name': 'Route Far',
            'warehouse_id': self.warehouse_1.id,
            'latitude': 47.82093,
            'longitude': -122.31513,
        })

    def test_planner_creation(self):
        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_1.id,
            'name': 'demo',
        })
        both_wh_ids = self.both_wh_ids()
        planner = self.env['sale.order.make.plan'].with_context(warehouse_domain=[('id', 'in', both_wh_ids)],
                                                                skip_plan_shipping=True).create({'order_id': self.so.id})
        self.assertTrue(planner.planning_option_ids, 'Must have one or more plans.')
        self.assertEqual(planner.planning_option_ids.delivery_route_id, self.route_near)
        self.so.partner_id.partner_latitude = 47.82093
        planner = self.env['sale.order.make.plan'].with_context(warehouse_domain=[('id', 'in', both_wh_ids)],
                                                                skip_plan_shipping=True).create({'order_id': self.so.id})
        self.assertEqual(planner.planning_option_ids.delivery_route_id, self.route_far)
