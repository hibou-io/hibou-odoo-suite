
from odoo.tests.common import Form, TransactionCase
from odoo.exceptions import UserError


class TestPurolator(TransactionCase):
    def setUp(self):
        super().setUp()
        self.carrier = self.env.ref('delivery_purolator.purolator_ground', raise_if_not_found=False)
        if not self.carrier or not self.carrier.purolator_api_key:
            self.skipTest('Purolator Shipping not configured, skipping tests.')
        if self.carrier.prod_environment:
            self.skipTest('Purolator Shipping configured to use production credentials, skipping tests.')
        
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
        })
        self.receiver_partner = self.env['res.partner'].create({
            'name': 'Receiver Address',
            'city': 'Burnaby',
            'street': '1234 Test Rd.',
            'state_id': self.ref('base.state_ca_bc'),
            'country_id': self.ref('base.ca'),
            'zip': 'V5C5A9',
        })
        self.storage_box = self.env.ref('product.product_product_6')
        self.storage_box.weight = 1.5  # Something more reasonable
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
        
        # reconfigure this method so that we can set its default package to one that needs a service code
        self.delivery_carrier_ground = self.env.ref('delivery_purolator.purolator_ground')
        self.delivery_carrier_ground.purolator_default_package_type_id = self.env.ref('delivery_purolator.purolator_packaging_large_package')
        # set a VERY low requirement for signature
        self.delivery_carrier_ground.automatic_insurance_value = 0.1
        self.delivery_carrier_ground.automatic_sig_req_value = 0.1
    
    def _so_pick_shipping(self):
            # Regular Update Shipping functionality
        delivery_wizard = Form(self.env['choose.delivery.carrier'].with_context({
                'default_order_id': self.sale_order.id,
                'default_carrier_id': self.ref('delivery_purolator.purolator_ground'),
        }))
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.update_price()
        self.assertGreater(choose_delivery_carrier.delivery_price, 0.0, "Purolator delivery cost for this SO has not been correctly estimated.")
        choose_delivery_carrier.button_confirm()
        self.assertEqual(self.sale_order.carrier_id, self.carrier)
    
    def test_00_rate_order(self):
        self._so_pick_shipping()

        # Multi-rating with sale order
        rates = self.carrier.rate_shipment_multi(order=self.sale_order)
        carrier_express = self.env.ref('delivery_purolator.purolator_express')
        rate_express = list(filter(lambda r: r['carrier'] == carrier_express, rates))
        rate_express = rate_express and rate_express[0]
        self.assertFalse(rate_express['error_message'])
        self.assertGreater(rate_express['price'], 0.0)
        self.assertGreater(rate_express['transit_days'], 0)
        self.assertEqual(rate_express['package'], self.env['stock.quant.package'].browse())
        
        # Multi-rating with picking
        self.sale_order.action_confirm()
        picking = self.sale_order.picking_ids
        self.assertEqual(len(picking), 1)
        rates = self.carrier.rate_shipment_multi(picking=picking)
        rate_express = list(filter(lambda r: r['carrier'] == carrier_express, rates))
        rate_express = rate_express and rate_express[0]
        self.assertFalse(rate_express['error_message'])
        self.assertGreater(rate_express['price'], 0.0)
        self.assertGreater(rate_express['transit_days'], 0)
        self.assertEqual(rate_express['package'], self.env['stock.quant.package'].browse())
        
        # Multi-rate package
        self.assertEqual(picking.move_lines.reserved_availability, 3.0)
        picking.move_line_ids.qty_done = 1.0
        context = dict(
            current_package_carrier_type=picking.carrier_id.delivery_type,
            default_picking_id=picking.id
        )
        choose_package_wizard = self.env['choose.delivery.package'].with_context(context).create({})
        self.assertEqual(choose_package_wizard.shipping_weight, 1.5)
        choose_package_wizard.action_put_in_pack()
        package = picking.move_line_ids.mapped('result_package_id')
        self.assertEqual(len(package), 1)
        
        rates = self.carrier.rate_shipment_multi(picking=picking, packages=package)
        rate_express = list(filter(lambda r: r['carrier'] == carrier_express, rates))
        rate_express = rate_express and rate_express[0]
        self.assertFalse(rate_express['error_message'])
        self.assertGreater(rate_express['price'], 0.0)
        self.assertGreater(rate_express['transit_days'], 0)
        self.assertEqual(rate_express['package'], package)

    def test_20_shipping(self):
        self._so_pick_shipping()
        self.sale_order.action_confirm()
        picking = self.sale_order.picking_ids
        self.assertEqual(picking.carrier_id, self.carrier)
        self.assertEqual(picking.message_attachment_count, 0)
        
        # Test Error handling:
        # Not having a city will result in an error
        original_shipper_partner_city = self.shipper_partner.city
        self.shipper_partner.city = ''
        with self.assertRaises(UserError):
            picking.send_to_shipper()
        self.shipper_partner.city = original_shipper_partner_city

        # Basic case: no qty done or packages or anything at all really
        # it makes sense to be able to do 'something' in this case
        picking.carrier_price = 50.0
        picking.send_to_shipper()
        self.assertTrue(picking.carrier_tracking_ref)
        self.assertEqual(picking.message_attachment_count, 1)  # has tracking label now
        self.assertEqual(picking.carrier_price, 50.0) # price is set during planning and should remain unchanged
        
        # Void
        picking.cancel_shipment()
        self.assertFalse(picking.carrier_tracking_ref)
