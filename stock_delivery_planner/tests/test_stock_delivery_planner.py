from odoo import fields
from odoo.tests.common import Form, TransactionCase


class TestStockDeliveryPlanner(TransactionCase):
    def setUp(self):
        """
        NOTE: demo Fedex credentials may not work. Test credentials may not return all service types.
        Configuring production credentials may be necessary for this test to run.
        """
        super(TestStockDeliveryPlanner, self).setUp()
        try:
            self.fedex_ground = self.browse_ref('delivery_fedex.delivery_carrier_fedex_us')
        except ValueError:
            self.skipTest('FedEx Shipping Connector demo data is required to run this test.')
        self.env['ir.config_parameter'].sudo().set_param('sale.order.planner.carrier_domain',
                                                         "[('id', 'in', (%d,))]" % self.fedex_ground.id)
        self.env['ir.config_parameter'].sudo().set_param('stock.delivery.planner.carrier_domain',
                                                         "[('id', 'in', (%d,))]" % self.fedex_ground.id)
        # Does it make sense to set default package in fedex_rate_shipment_multi
        # instead of relying on a correctly configured delivery method?
        self.fedex_package = self.browse_ref('delivery_fedex.fedex_packaging_FEDEX_25KG_BOX')
        self.default_package = self.browse_ref('delivery_fedex.fedex_packaging_YOUR_PACKAGING')
        self.fedex_ground.fedex_default_packaging_id = self.default_package
        # PRIORITY_OVERNIGHT might not be available depending on time of day?
        self.fedex_ground.fedex_service_type = 'FEDEX_GROUND'

        self.fedex_2_day = self.fedex_ground.copy()
        self.fedex_2_day.name = 'Test FedEx Delivery'
        self.fedex_2_day.fedex_service_type = 'FEDEX_2_DAY'

        delivery_calendar = self.env['resource.calendar'].create({
            'name': 'Test Delivery Calendar',
            'tz': 'US/Central',
            'attendance_ids': [
                (0, 0, {'name': 'Monday', 'dayofweek': '0', 'hour_from': 0, 'hour_to': 24, 'day_period': 'morning'}),
                (0, 0, {'name': 'Tuesday', 'dayofweek': '1', 'hour_from': 0, 'hour_to': 24, 'day_period': 'morning'}),
                (0, 0, {'name': 'Wednesday', 'dayofweek': '2', 'hour_from': 0, 'hour_to': 24, 'day_period': 'morning'}),
                (0, 0, {'name': 'Thursday', 'dayofweek': '3', 'hour_from': 0, 'hour_to': 24, 'day_period': 'morning'}),
                (0, 0, {'name': 'Friday', 'dayofweek': '4', 'hour_from': 0, 'hour_to': 24, 'day_period': 'morning'}),
            ],
        })
        self.fedex_ground.delivery_calendar_id = delivery_calendar
        self.fedex_2_day.delivery_calendar_id = delivery_calendar
        self.env['stock.warehouse'].search([]).write({'shipping_calendar_id': delivery_calendar.id})

        # needs a valid address for sender and recipient
        self.country_usa = self.env['res.country'].search([('name', '=', 'United States')], limit=1)
        self.state_wa = self.env['res.country.state'].search([('name', '=', 'Washington')], limit=1)
        self.state_ia = self.env['res.country.state'].search([('name', '=', 'Iowa')], limit=1)
        self.env.user.company_id.partner_id.write({
            'street': '321 1st St',
            'city': 'Ames',
            'state_id': self.state_ia.id,
            'zip': '50010',
            'country_id': self.country_usa.id,
        })
        pricelist = self.browse_ref('product.list0').copy({
            'currency_id': self.env.ref('base.USD').id,
            'sequence': 999,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'street': '1234 Test Street',
            'city': 'Marysville',
            'state_id': self.state_wa.id,
            'zip': '98270',
            'country_id': self.country_usa.id,
            'property_product_pricelist': pricelist.id,
            'is_company': True,
            # 'partner_latitude': 48.05636,
            # 'partner_longitude': -122.14922,
        })

        # self.product = self.browse_ref('product.product_product_27')  # [FURN_8855] Drawer
        # self.product.weight = 5.0
        # self.product.volume = 0.1
        self.env['ir.config_parameter'].sudo().set_param('product.weight_in_lbs', '1')
        self.product = self.env['product.product'].create({
            'name': 'Test Ship Product',
            'type': 'product',
            'weight': 1.0,
        })
        self.env['stock.change.product.qty'].create({
            'product_id': self.product.id,
            'product_tmpl_id': self.product.product_tmpl_id.id,
            'new_quantity': 10.0,
        }).change_product_qty()

        so = Form(self.env['sale.order'])
        so.partner_id = self.partner
        with so.order_line.new() as line:
            line.product_id = self.product
            line.product_uom_qty = 5.0
            line.price_unit = 100.0
        self.sale_order = so.save()

        order_plan_action = self.sale_order.action_planorder()
        order_plan = self.env[order_plan_action['res_model']].browse(order_plan_action['res_id'])
        order_plan.planning_option_ids.filtered(lambda o: o.carrier_id == self.fedex_ground).select_plan()

        self.sale_order.action_confirm()
        self.picking = self.sale_order.picking_ids

    def test_00_test_one_package(self):
        """Delivery is packed in one package"""
        self.assertTrue(self.sale_order.requested_date, 'Order has not been planned')
        self.assertEqual(len(self.picking), 1)
        grp_pack = self.env.ref('stock.group_tracking_lot')
        self.env.user.write({'groups_id': [(4, grp_pack.id)]})

        self.assertEqual(self.picking.carrier_id, self.fedex_ground, 'Carrier did not carry over to Delivery Order')
        self.assertEqual(self.picking.weight, 5.0)
        self.assertEqual(self.picking.shipping_weight, 0.0)

        self.picking.move_line_ids.filtered(lambda ml: ml.product_id == self.product).qty_done = 5.0
        packing_action = self.picking.action_put_in_pack()
        packing_wizard = Form(self.env[packing_action['res_model']].with_context(packing_action['context']))
        packing_wizard.delivery_packaging_id = self.fedex_package
        choose_delivery_package = packing_wizard.save()
        choose_delivery_package.action_put_in_pack()
        self.assertEqual(self.picking.shipping_weight, 5.0)

        action = self.picking.action_plan_delivery()
        planner = self.env[action['res_model']].browse(action['res_id'])

        self.assertEqual(planner.picking_id, self.picking)
        self.assertGreater(len(planner.plan_option_ids), 1)

        plan_option = planner.plan_option_ids.filtered(lambda o: o.carrier_id == self.fedex_2_day)
        self.assertEqual(len(plan_option), 1)
        self.assertGreater(plan_option.price, 0.0)
        self.assertEqual(plan_option.date_planned.date(), fields.Date().today())
        self.assertTrue(plan_option.requested_date)
        self.assertEqual(plan_option.transit_days, 2)
        self.assertEqual(plan_option.sale_requested_date, self.sale_order.requested_date)
        # Order Planner expects to ship tomorrow: we are shipping a day early and using
        # 2-day shipping instead of 3, giving us 2 days difference
        self.assertEqual(plan_option.days_different, -2.0)

        plan_option.select_plan()
        self.assertEqual(self.picking.carrier_id, self.fedex_2_day)
