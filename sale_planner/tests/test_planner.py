from odoo.tests import common
from datetime import datetime, timedelta


class TestPlanner(common.TransactionCase):
    # @todo Test date planning!

    def setUp(self):
        super(TestPlanner, self).setUp()
        self.today = datetime.today()
        self.tomorrow = datetime.today() + timedelta(days=1)
        # This partner has a parent
        self.country_usa = self.env['res.country'].search([('name', '=', 'United States')], limit=1)
        self.state_wa = self.env['res.country.state'].search([('name', '=', 'Washington')], limit=1)
        self.state_co = self.env['res.country.state'].search([('name', '=', 'Colorado')], limit=1)
        self.partner_wa = self.env['res.partner'].create({
            'name': 'Jared',
            'street': '1234 Test Street',
            'city': 'Marysville',
            'state_id': self.state_wa.id,
            'zip': '98270',
            'country_id': self.country_usa.id,
            'partner_latitude': 48.05636,
            'partner_longitude': -122.14922,
        })
        self.warehouse_partner_1 = self.env['res.partner'].create({
            'name': 'WH1',
            'street': '1234 Test Street',
            'city': 'Lynnwood',
            'state_id': self.state_wa.id,
            'zip': '98036',
            'country_id': self.country_usa.id,
            'partner_latitude': 47.82093,
            'partner_longitude': -122.31513,
        })

        self.warehouse_partner_2 = self.env['res.partner'].create({
            'name': 'WH2',
            'street': '1234 Test Street',
            'city': 'Craig',
            'state_id': self.state_co.id,
            'zip': '81625',
            'country_id': self.country_usa.id,
            'partner_latitude': 40.51525,
            'partner_longitude': -107.54645,
        })
        self.warehouse_calendar_1 = self.env['resource.calendar'].create({
            'name': 'Washington Warehouse Hours',
            'attendance_ids': [
                (0, 0, {'name': 'today',
                        'dayofweek': str(self.today.weekday()),
                        'hour_from': (self.today.hour - 1) % 24,
                        'hour_to': (self.today.hour + 1) % 24}),
                (0, 0, {'name': 'tomorrow',
                        'dayofweek': str(self.tomorrow.weekday()),
                        'hour_from': (self.tomorrow.hour - 1) % 24,
                        'hour_to': (self.tomorrow.hour + 1) % 24}),
            ]
        })
        self.warehouse_calendar_2 = self.env['resource.calendar'].create({
            'name': 'Colorado Warehouse Hours',
            'attendance_ids': [
                (0, 0, {'name': 'tomorrow',
                        'dayofweek': str(self.tomorrow.weekday()),
                        'hour_from': (self.tomorrow.hour - 1) % 24,
                        'hour_to': (self.tomorrow.hour + 1) % 24}),
            ]
        })
        self.warehouse_1 = self.env['stock.warehouse'].create({
            'name': 'Washington Warehouse',
            'partner_id': self.warehouse_partner_1.id,
            'code': 'WH1',
            'shipping_calendar_id': self.warehouse_calendar_1.id,
        })
        self.warehouse_2 = self.env['stock.warehouse'].create({
            'name': 'Colorado Warehouse',
            'partner_id': self.warehouse_partner_2.id,
            'code': 'WH2',
            'shipping_calendar_id': self.warehouse_calendar_2.id,
        })
        self.so = self.env['sale.order'].create({
            'partner_id': self.partner_wa.id,
            'warehouse_id': self.warehouse_1.id,
        })
        self.product_1 = self.env['product.template'].create({
            'name': 'Product for WH1',
            'type': 'product',
            'standard_price': 1.0,
        })
        self.product_1 = self.product_1.product_variant_id
        self.product_2 = self.env['product.template'].create({
            'name': 'Product for WH2',
            'type': 'product',
            'standard_price': 1.0,
        })
        self.product_2 = self.product_2.product_variant_id
        self.product_both = self.env['product.template'].create({
            'name': 'Product for Both',
            'type': 'product',
            'standard_price': 1.0,
        })
        self.product_both = self.product_both.product_variant_id
        self.env['stock.change.product.qty'].create({
            'location_id': self.warehouse_1.lot_stock_id.id,
            'product_id': self.product_1.id,
            'new_quantity': 100,
        }).change_product_qty()
        self.env['stock.change.product.qty'].create({
            'location_id': self.warehouse_1.lot_stock_id.id,
            'product_id': self.product_both.id,
            'new_quantity': 100,
        }).change_product_qty()
        self.env['stock.change.product.qty'].create({
            'location_id': self.warehouse_2.lot_stock_id.id,
            'product_id': self.product_2.id,
            'new_quantity': 100,
        }).change_product_qty()
        self.env['stock.change.product.qty'].create({
            'location_id': self.warehouse_2.lot_stock_id.id,
            'product_id': self.product_both.id,
            'new_quantity': 100,
        }).change_product_qty()

    def both_wh_ids(self):
        return [self.warehouse_1.id, self.warehouse_2.id]

    def test_planner_creation_internals(self):
        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_1.id,
            'name': 'demo',
        })
        both_wh_ids = self.both_wh_ids()
        planner = self.env['sale.order.make.plan'].with_context(warehouse_domain=[('id', 'in', both_wh_ids)], skip_plan_shipping=True).create({'order_id': self.so.id})
        self.assertEqual(set(both_wh_ids), set(planner.get_warehouses().ids))
        fake_order = planner._fake_order(self.so)
        base_option = planner.generate_base_option(fake_order)
        self.assertTrue(base_option, 'Must have base option.')
        self.assertEqual(self.warehouse_1.id, base_option['warehouse_id'])

    def test_planner_creation(self):
        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_1.id,
            'name': 'demo',
        })
        self.assertEqual(self.product_1.with_context(warehouse=self.warehouse_1.id).qty_available, 100)
        self.assertEqual(self.product_1.with_context(warehouse=self.warehouse_2.id).qty_available, 0)
        both_wh_ids = self.both_wh_ids()
        planner = self.env['sale.order.make.plan'].with_context(warehouse_domain=[('id', 'in', both_wh_ids)], skip_plan_shipping=True).create({'order_id': self.so.id})
        self.assertTrue(planner.planning_option_ids, 'Must have one or more plans.')
        self.assertEqual(planner.planning_option_ids.warehouse_id, self.warehouse_1)
        self.assertFalse(planner.planning_option_ids[0].sub_options)

    def test_planner_creation_2(self):
        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_2.id,
            'name': 'demo',
        })
        self.assertEqual(self.product_2.with_context(warehouse=self.warehouse_1.id).qty_available, 0)
        self.assertEqual(self.product_2.with_context(warehouse=self.warehouse_2.id).qty_available, 100)
        both_wh_ids = self.both_wh_ids()
        planner = self.env['sale.order.make.plan'].with_context(warehouse_domain=[('id', 'in', both_wh_ids)], skip_plan_shipping=True).create({'order_id': self.so.id})
        self.assertTrue(planner.planning_option_ids, 'Must have one or more plans.')
        self.assertEqual(planner.planning_option_ids.warehouse_id, self.warehouse_2)
        self.assertFalse(planner.planning_option_ids[0].sub_options)

    def test_planner_creation_split(self):
        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_1.id,
            'name': 'demo',
        })
        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_2.id,
            'name': 'demo',
        })
        self.assertEqual(self.product_1.with_context(warehouse=self.warehouse_1.id).qty_available, 100)
        self.assertEqual(self.product_2.with_context(warehouse=self.warehouse_2.id).qty_available, 100)
        both_wh_ids = self.both_wh_ids()
        planner = self.env['sale.order.make.plan'].with_context(warehouse_domain=[('id', 'in', both_wh_ids)], skip_plan_shipping=True).create({'order_id': self.so.id})
        self.assertTrue(planner.planning_option_ids, 'Must have one or more plans.')
        self.assertTrue(planner.planning_option_ids[0].sub_options)

    def test_planner_creation_no_split(self):
        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_both.id,
            'name': 'demo',
        })
        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_2.id,
            'name': 'demo',
        })
        self.assertEqual(self.product_both.with_context(warehouse=self.warehouse_2.id).qty_available, 100)
        self.assertEqual(self.product_2.with_context(warehouse=self.warehouse_2.id).qty_available, 100)
        both_wh_ids = self.both_wh_ids()
        planner = self.env['sale.order.make.plan'].with_context(warehouse_domain=[('id', 'in', both_wh_ids)], skip_plan_shipping=True).create({'order_id': self.so.id})
        self.assertTrue(planner.planning_option_ids, 'Must have one or more plans.')
        self.assertEqual(planner.planning_option_ids.warehouse_id, self.warehouse_2)
        self.assertFalse(planner.planning_option_ids[0].sub_options)
