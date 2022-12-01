# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo.tests.common import Form, TransactionCase


class TestDeliveryPurolatorPlannerPrice(TransactionCase):
    def setUp(self):
        super().setUp()
        self.carrier = self.env.ref('delivery_purolator.purolator_ground', raise_if_not_found=False)
        if not self.carrier or not self.carrier.purolator_api_key:
            self.skipTest('Purolator Shipping not configured, skipping tests.')
        if self.carrier.prod_environment:
            self.skipTest('Purolator Shipping configured to use production credentials, skipping tests.')

        # Order planner setup
        self.env['ir.config_parameter'].sudo().set_param('sale.planner.carrier_ids.%s' % (self.env.company.id, ),
                                                         "%d" % self.carrier.id)
        self.env['ir.config_parameter'].sudo().set_param('stock.delivery.planner.carrier_ids.%s' % (self.env.company.id, ),
                                                         "%d" % self.carrier.id)
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
        self.carrier.delivery_calendar_id = delivery_calendar
        # self.fedex_2_day.delivery_calendar_id = delivery_calendar
        # self.env['stock.warehouse'].search([]).write({'shipping_calendar_id': delivery_calendar.id})
        
        # the setup for these addresses is important as there is
        # error handling on purolator's side
        self.state_ca_ontario = self.env.ref('base.state_ca_on')
        self.country_ca = self.state_ca_ontario.country_id
        
        self.shipper_partner = self.env['res.partner'].create({
            'name': 'The Great North Ltd.',
            'zip': 'L4W5M8',
            'street': '1234 Test St.',
            'state_id': self.state_ca_ontario.id,
            'country_id': self.country_ca.id,
            'city': 'Mississauga',  # note other city will return error for this field+zip
        })
        self.shipper_warehouse = self.env['stock.warehouse'].create({
            'partner_id': self.shipper_partner.id,
            'name': 'Canadian Warehouse',
            'code': 'CWH',
            'shipping_calendar_id': delivery_calendar.id,
        })
        self.env['ir.config_parameter'].sudo().set_param('sale.planner.warehouse_ids.%s' % (self.env.company.id, ),
                                                         "%d" % self.shipper_warehouse.id)
        self.receiver_partner = self.env['res.partner'].create({
            'name': 'Receiver Address',
            'city': 'Burnaby',
            'street': '1234 Test Rd.',
            'state_id': self.ref('base.state_ca_bc'),
            'country_id': self.ref('base.ca'),
            'zip': 'V5C5A9',
        })
        self.storage_box = self.env.ref('product.product_product_6')
        self.storage_box.weight = 1.0  # Something more reasonable
        # Make some available
        self.env['stock.quant']._update_available_quantity(self.storage_box, self.shipper_warehouse.lot_stock_id, 100)
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.receiver_partner.id,
            'warehouse_id': self.shipper_warehouse.id,
            'order_line': [(0, 0, {
                'name': self.storage_box.name,
                'product_id': self.storage_box.id,
                'product_uom_qty': 3.0,
                'product_uom': self.storage_box.uom_id.id,
                'price_unit': self.storage_box.lst_price,
            })],
        })
        order_plan_action = self.sale_order.action_planorder()
        order_plan = self.env[order_plan_action['res_model']].browse(order_plan_action['res_id'])
        order_plan.planning_option_ids.filtered(lambda o: o.carrier_id == self.carrier).select_plan()

        self.sale_order.action_confirm()
        self.picking = self.sale_order.picking_ids
        
    def test_00_estimate_shipping_cost(self):
        self.assertEqual(self.picking.carrier_id, self.carrier, 'Carrier did not carry over to Delivery Order')
        
        self.picking.move_line_ids.filtered(lambda ml: ml.product_id == self.storage_box).qty_done = 3.0
        packing_action = self.picking.action_put_in_pack()
        packing_wizard = Form(self.env[packing_action['res_model']].with_context(packing_action['context']))
        choose_delivery_package = packing_wizard.save()
        choose_delivery_package.action_put_in_pack()
        self.assertEqual(self.picking.shipping_weight, 3.0)

        action = self.picking.action_plan_delivery()
        planner = self.env[action['res_model']].browse(action['res_id'])

        self.assertEqual(planner.picking_id, self.picking)
        self.assertGreater(len(planner.plan_option_ids), 1)

        plan_option = planner.plan_option_ids.filtered(lambda o: o.carrier_id == self.carrier)
        self.assertEqual(len(plan_option), 1)
        self.assertGreater(plan_option.price, 0.0)
        
        plan_option.select_plan()
        planner.action_plan()
        self.assertEqual(self.picking.carrier_id, self.carrier)
        self.assertEqual(plan_option.price, self.picking.carrier_price)
