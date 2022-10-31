
from odoo.tests.common import Form, TransactionCase
from odoo.exceptions import UserError


class CommonTestCarrier(TransactionCase):
    def setUp(self):
        super().setUp()
        # fill in your carrier in setUp
        self.carrier = False
        
        self.state_us_wa = self.env.ref('base.state_us_48')
        self.country_us = self.state_us_wa.country_id
        
        self.shipper_partner = self.env['res.partner'].create({
            'name': 'Start Warehouse',
            'street': '2901 174th St. NE',
            'city': 'Marysville',  # note other city will return error for this field+zip
            'state_id': self.state_us_wa.id,
            'country_id': self.country_us.id,
            'zip': '98271',
        })
        self.shipper_warehouse = self.env['stock.warehouse'].create({
            'partner_id': self.shipper_partner.id,
            'name': 'US Warehouse',
            'code': 'TWH',
        })
        self.receiver_partner = self.env['res.partner'].create({
            'name': 'Receiver Address',
            'street': '336 Chardonnay Ave.',
            'street2': 'Suite A',
            'city': 'Prosser',
            'state_id': self.state_us_wa.id,
            'country_id': self.country_us.id,
            'zip': '99350',
        })
        self.order_product = self.env['product.product'].create({
            'name': 'Test physical product',
            'type': 'product',
            'weight': 1.5,
            'volume': 0.8,
        })
        # Make some available
        self.env['stock.quant']._update_available_quantity(self.order_product, self.shipper_warehouse.lot_stock_id, 100)
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.receiver_partner.id,
            'warehouse_id': self.shipper_warehouse.id,
            'order_line': [(0, 0, {
                'name': self.order_product.name,
                'product_id': self.order_product.id,
                'product_uom_qty': 3.0,
                'product_uom': self.order_product.uom_id.id,
                'price_unit': self.order_product.lst_price,
            })],
        })
    
    def _so_pick_shipping(self, default_carrier_id=False):
            # Regular Update Shipping functionality
        delivery_wizard = Form(self.env['choose.delivery.carrier'].with_context({
                'default_order_id': self.sale_order.id,
                'default_carrier_id': default_carrier_id or self.carrier.id,
        }))
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.update_price()
        self.assertGreater(choose_delivery_carrier.delivery_price, 0.0, "No delivery price during carrier selection.")
        choose_delivery_carrier.button_confirm()
        self.assertEqual(self.sale_order.carrier_id, self.carrier)
    
    def _test_01_assert_rate_shipment_multi_rates_order(self, rates, order):
        self.assertTrue(rates)
    
    def _test_01_assert_rate_shipment_multi_rates_picking(self, rates, picking):
        self.assertTrue(rates)
    
    def _test_01_assert_rate_shipment_multi_rates_package(self, rates, picking, package):
        self.assertTrue(rates)
    
    def test_01_rate_order(self):
        if not self.carrier:
            return
        self._so_pick_shipping()

        # Multi-rating with sale order
        rates = self.carrier.rate_shipment_multi(order=self.sale_order)
        self._test_01_assert_rate_shipment_multi_rates_order(rates, self.sale_order)
        
        # Multi-rating with picking
        self.sale_order.action_confirm()
        picking = self.sale_order.picking_ids
        self.assertEqual(len(picking), 1)
        rates = self.carrier.rate_shipment_multi(picking=picking)
        self._test_01_assert_rate_shipment_multi_rates_picking(rates, picking)
        
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
        self._test_01_assert_rate_shipment_multi_rates_package(rates, picking, package)

    def _test_02_assert_post_send_to_shipper(self, picking):
        self.assertTrue(picking.carrier_tracking_ref)
        self.assertEqual(picking.message_attachment_count, 1)
        self.assertGreater(picking.carrier_price, 0.0)
    
    def _test_02_assert_post_cancel_shipment(self, picking):
        self.assertFalse(picking.carrier_tracking_ref)

    def test_02_shipping(self):
        if not self.carrier:
            return
        self._so_pick_shipping()
        self.sale_order.action_confirm()
        picking = self.sale_order.picking_ids
        self.assertEqual(picking.carrier_id, self.carrier)
        self.assertEqual(picking.message_attachment_count, 0)
        
        picking.send_to_shipper()
        self._test_02_assert_post_send_to_shipper(picking)
        
        # Void
        picking.cancel_shipment()
        self._test_02_assert_post_cancel_shipment(picking)
