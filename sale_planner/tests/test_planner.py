from odoo.tests import common
from datetime import datetime, timedelta
from json import loads as json_decode
from logging import getLogger

_logger = getLogger(__name__)


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
        hour_from = (self.today.hour - 1) % 24
        hour_to = (self.today.hour + 1) % 24
        if hour_to < hour_from:
            hour_to, hour_from = hour_from, hour_to

        self.warehouse_calendar_1 = self.env['resource.calendar'].create({
            'name': 'Washington Warehouse Hours',
            'tz': 'UTC',
            'attendance_ids': [
                (0, 0, {'name': 'today',
                        'dayofweek': str(self.today.weekday()),
                        'hour_from': hour_from,
                        'hour_to': hour_to,
                        'day_period': 'morning'}),

                (0, 0, {'name': 'tomorrow',
                        'dayofweek': str(self.tomorrow.weekday()),
                        'hour_from': hour_from,
                        'hour_to': hour_to,
                        'day_period': 'morning'}),

            ]
        })
        self.warehouse_calendar_2 = self.env['resource.calendar'].create({
            'name': 'Colorado Warehouse Hours',
            'tz': 'UTC',
            'attendance_ids': [
                (0, 0, {'name': 'tomorrow',
                        'dayofweek': str(self.tomorrow.weekday()),
                        'hour_from': hour_from,
                        'hour_to': hour_to,
                        'day_period': 'morning'}),
            ]
        })
        self.warehouse_1 = self.env['stock.warehouse'].create({
            'name': 'Washington Warehouse',
            'partner_id': self.warehouse_partner_1.id,
            'code': 'TWH1',
            'shipping_calendar_id': self.warehouse_calendar_1.id,
        })
        self.warehouse_2 = self.env['stock.warehouse'].create({
            'name': 'Colorado Warehouse',
            'partner_id': self.warehouse_partner_2.id,
            'code': 'TWH2',
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
        self.product_12 = self.env['product.template'].create({
            'name': 'Product for WH1 Second',
            'type': 'product',
            'standard_price': 1.0,
        })
        self.product_1 = self.product_1.product_variant_id
        self.product_12 = self.product_12.product_variant_id
        self.product_2 = self.env['product.template'].create({
            'name': 'Product for WH2',
            'type': 'product',
            'standard_price': 1.0,
        })
        self.product_22 = self.env['product.template'].create({
            'name': 'Product for WH2 Second',
            'type': 'product',
            'standard_price': 1.0,
        })
        self.product_2 = self.product_2.product_variant_id
        self.product_22 = self.product_22.product_variant_id
        self.product_both = self.env['product.template'].create({
            'name': 'Product for Both',
            'type': 'product',
            'standard_price': 1.0,
        })
        self.product_both = self.product_both.product_variant_id
        self.env['stock.quant'].create({
            'location_id': self.warehouse_1.lot_stock_id.id,
            'product_id': self.product_1.id,
            'quantity': 100,
        })
        self.env['stock.quant'].create({
            'location_id': self.warehouse_1.lot_stock_id.id,
            'product_id': self.product_12.id,
            'quantity': 100,
        })
        self.env['stock.quant'].create({
            'location_id': self.warehouse_1.lot_stock_id.id,
            'product_id': self.product_both.id,
            'quantity': 100,
        })
        self.env['stock.quant'].create({
            'location_id': self.warehouse_2.lot_stock_id.id,
            'product_id': self.product_2.id,
            'quantity': 100,
        })
        self.env['stock.quant'].create({
            'location_id': self.warehouse_2.lot_stock_id.id,
            'product_id': self.product_22.id,
            'quantity': 100,
        })
        self.env['stock.quant'].create({
            'location_id': self.warehouse_2.lot_stock_id.id,
            'product_id': self.product_both.id,
            'quantity': 100,
        })

        self.policy_closest = self.env['sale.order.planning.policy'].create({
            'always_closest_warehouse': True,
        })
        self.policy_other = self.env['sale.order.planning.policy'].create({})
        self.wh_filter_1 = self.env['ir.filters'].create({
            'name': 'TWH1 Only',
            'domain': "[('id', '=', %d)]" % (self.warehouse_1.id, ),
            'model_id': 'stock.warehouse',
        })
        self.wh_filter_2 = self.env['ir.filters'].create({
            'name': 'TWH2 Only',
            'domain': "[('id', '=', %d)]" % (self.warehouse_2.id,),
            'model_id': 'stock.warehouse',
        })
        self.policy_wh_1 = self.env['sale.order.planning.policy'].create({
            'warehouse_filter_id': self.wh_filter_1.id,
        })
        self.policy_wh_2 = self.env['sale.order.planning.policy'].create({
            'warehouse_filter_id': self.wh_filter_2.id,
        })

    def both_wh_ids(self):
        return [self.warehouse_1.id, self.warehouse_2.id]

    def test_10_planner_creation_internals(self):
        """
        Tests certain internal representations and that we can create a basic plan.
        """
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

    def test_21_planner_creation(self):
        """
        Scenario where only one warehouse has inventory on the order line.
        This is "the closest" warehouse.
        """
        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_1.id,
            'name': 'demo',
        })
        self.assertEqual(self.product_1.with_context(warehouse=self.warehouse_2.id).qty_available, 0)
        self.product_1.invalidate_cache(fnames=['qty_available'], ids=self.product_1.ids)
        self.assertEqual(self.product_1.with_context(warehouse=self.warehouse_1.id).qty_available, 100)
        self.product_1.invalidate_cache(fnames=['qty_available'], ids=self.product_1.ids)

        both_wh_ids = self.both_wh_ids()
        planner = self.env['sale.order.make.plan'].with_context(warehouse_domain=[('id', 'in', both_wh_ids)], skip_plan_shipping=True).create({'order_id': self.so.id})
        self.assertTrue(planner.planning_option_ids, 'Must have one or more plans.')
        self.assertEqual(planner.planning_option_ids.warehouse_id, self.warehouse_1)
        self.assertFalse(planner.planning_option_ids[0].sub_options)

    def test_22_planner_creation(self):
        """
        Scenario where only one warehouse has inventory on the order line.
        This is "the further" warehouse.
        """
        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_2.id,
            'name': 'demo',
        })
        self.assertEqual(self.product_2.with_context(warehouse=self.warehouse_1.id).qty_available, 0)
        self.product_2.invalidate_cache(fnames=['qty_available'], ids=self.product_2.ids)
        self.assertEqual(self.product_2.with_context(warehouse=self.warehouse_2.id).qty_available, 100)
        self.product_2.invalidate_cache(fnames=['qty_available'], ids=self.product_2.ids)
        both_wh_ids = self.both_wh_ids()
        planner = self.env['sale.order.make.plan'].with_context(warehouse_domain=[('id', 'in', both_wh_ids)], skip_plan_shipping=True).create({'order_id': self.so.id})
        self.assertTrue(planner.planning_option_ids, 'Must have one or more plans.')
        self.assertEqual(planner.planning_option_ids.warehouse_id, self.warehouse_2)
        self.assertFalse(planner.planning_option_ids[0].sub_options)

    def test_31_planner_creation_split(self):
        """
        Scenario where only one warehouse has inventory on each of the order line.
        This will cause two pickings to be created, one for each warehouse.
        """
        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_1.id,
            'name': 'demo',
        })
        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_2.id,
            'name': 'demo2',
        })
        self.assertEqual(self.product_1.with_context(warehouse=self.warehouse_1.id).qty_available, 100)
        self.assertEqual(self.product_2.with_context(warehouse=self.warehouse_2.id).qty_available, 100)
        both_wh_ids = self.both_wh_ids()
        planner = self.env['sale.order.make.plan'].with_context(warehouse_domain=[('id', 'in', both_wh_ids)], skip_plan_shipping=True).create({'order_id': self.so.id})
        self.assertTrue(planner.planning_option_ids, 'Must have one or more plans.')
        self.assertTrue(planner.planning_option_ids[0].sub_options)

    def test_32_planner_creation_no_split(self):
        """
        Scenario where only "the further" warehouse has inventory on whole order, but
        the "closest" warehouse only has inventory on one item.
        This will simply plan out of the "the further" warehouse.
        """
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

    def test_42_policy_force_closest(self):
        """
        Scenario where an item may not be in stock at "the closest" warehouse, but an item is only allowed
        to come from "the closest" warehouse.
        """
        self.product_2.property_planning_policy_id = self.policy_closest
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
        self.assertEqual(self.product_both.with_context(warehouse=self.warehouse_1.id).qty_available, 100)
        # Close warehouse doesn't have product.
        self.assertEqual(self.product_2.with_context(warehouse=self.warehouse_1.id).qty_available, 0)
        both_wh_ids = self.both_wh_ids()
        planner = self.env['sale.order.make.plan'].with_context(warehouse_domain=[('id', 'in', both_wh_ids)],
                                                                skip_plan_shipping=True).create({'order_id': self.so.id})
        self.assertTrue(planner.planning_option_ids, 'Must have one or more plans.')
        self.assertEqual(planner.planning_option_ids.warehouse_id, self.warehouse_1)
        self.assertFalse(planner.planning_option_ids[0].sub_options)

    def test_43_policy_merge(self):
        """
        Scenario that will make a complicated scenario specifically:
        - 3 policy groups
        - 2 base options with sub_options (all base options with same warehouse)
        """
        self.product_both.property_planning_policy_id = self.policy_closest
        self.product_12.property_planning_policy_id = self.policy_other
        self.product_22.property_planning_policy_id = self.policy_other

        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_both.id,
            'name': 'demo',
        })
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
        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_12.id,
            'name': 'demo',
        })
        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_22.id,
            'name': 'demo',
        })
        both_wh_ids = self.both_wh_ids()
        planner = self.env['sale.order.make.plan'].with_context(warehouse_domain=[('id', 'in', both_wh_ids)],
                                                                skip_plan_shipping=True).create({'order_id': self.so.id})
        self.assertTrue(planner.planning_option_ids, 'Must have one or more plans.')
        self.assertEqual(planner.planning_option_ids.warehouse_id, self.warehouse_1)
        self.assertTrue(planner.planning_option_ids.sub_options)

        sub_options = json_decode(planner.planning_option_ids.sub_options)
        _logger.error(sub_options)
        wh_1_ids = sorted([self.product_both.id, self.product_1.id, self.product_12.id])
        wh_2_ids = sorted([self.product_2.id, self.product_22.id])
        self.assertEqual(sorted(sub_options[str(self.warehouse_1.id)]['product_ids']), wh_1_ids)
        self.assertEqual(sorted(sub_options[str(self.warehouse_2.id)]['product_ids']), wh_2_ids)

    def test_44_policy_merge_2(self):
        """
        Scenario that will make a complicated scenario specifically:
        - 3 policy groups
        - 2 base options from different warehouses
        """
        self.product_both.property_planning_policy_id = self.policy_other
        self.product_12.property_planning_policy_id = self.policy_closest
        self.product_22.property_planning_policy_id = self.policy_other

        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_both.id,
            'name': 'demo',
        })
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
        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_12.id,
            'name': 'demo',
        })
        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_22.id,
            'name': 'demo',
        })
        both_wh_ids = self.both_wh_ids()
        planner = self.env['sale.order.make.plan'].with_context(warehouse_domain=[('id', 'in', both_wh_ids)],
                                                                skip_plan_shipping=True).create({'order_id': self.so.id})
        self.assertTrue(planner.planning_option_ids, 'Must have one or more plans.')
        self.assertEqual(planner.planning_option_ids.warehouse_id, self.warehouse_2)
        self.assertTrue(planner.planning_option_ids.sub_options)

        sub_options = json_decode(planner.planning_option_ids.sub_options)
        _logger.error(sub_options)
        wh_1_ids = sorted([self.product_1.id, self.product_12.id])
        wh_2_ids = sorted([self.product_both.id, self.product_2.id, self.product_22.id])
        self.assertEqual(sorted(sub_options[str(self.warehouse_1.id)]['product_ids']), wh_1_ids)
        self.assertEqual(sorted(sub_options[str(self.warehouse_2.id)]['product_ids']), wh_2_ids)

    def test_45_policy_merge_3(self):
        """
        Different order of products for test_44
        - 3 policy groups
        - 2 base options from different warehouses
        """
        self.product_both.property_planning_policy_id = self.policy_other
        self.product_12.property_planning_policy_id = self.policy_closest
        self.product_22.property_planning_policy_id = self.policy_other


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
        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_12.id,
            'name': 'demo',
        })
        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_22.id,
            'name': 'demo',
        })
        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_both.id,
            'name': 'demo',
        })
        both_wh_ids = self.both_wh_ids()
        planner = self.env['sale.order.make.plan'].with_context(warehouse_domain=[('id', 'in', both_wh_ids)],
                                                                skip_plan_shipping=True).create({'order_id': self.so.id})
        self.assertTrue(planner.planning_option_ids, 'Must have one or more plans.')
        self.assertEqual(planner.planning_option_ids.warehouse_id, self.warehouse_1)
        self.assertTrue(planner.planning_option_ids.sub_options)

        sub_options = json_decode(planner.planning_option_ids.sub_options)
        _logger.error(sub_options)
        wh_1_ids = sorted([self.product_1.id, self.product_12.id])
        wh_2_ids = sorted([self.product_both.id, self.product_2.id, self.product_22.id])
        self.assertEqual(sorted(sub_options[str(self.warehouse_1.id)]['product_ids']), wh_1_ids)
        self.assertEqual(sorted(sub_options[str(self.warehouse_2.id)]['product_ids']), wh_2_ids)

    def test_51_policy_specific_warehouse(self):
        """
        Force one item to TWH2.
        """
        self.product_both.property_planning_policy_id = self.policy_wh_2

        self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product_both.id,
            'name': 'demo',
        })
        both_wh_ids = self.both_wh_ids()
        planner = self.env['sale.order.make.plan'].with_context(warehouse_domain=[('id', 'in', both_wh_ids)],
                                                                skip_plan_shipping=True).create({'order_id': self.so.id})
        self.assertTrue(planner.planning_option_ids, 'Must have one or more plans.')
        self.assertEqual(planner.planning_option_ids.warehouse_id, self.warehouse_2)
