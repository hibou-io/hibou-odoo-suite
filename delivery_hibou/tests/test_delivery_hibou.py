from odoo.tests import common


class TestDeliveryHibou(common.TransactionCase):

    def setUp(self):
        super(TestDeliveryHibou, self).setUp()
        self.partner = self.env.ref('base.res_partner_address_13')
        self.product = self.env.ref('product.product_product_7')
        # Create Shipping Account
        self.shipping_account = self.env['partner.shipping.account'].create({
            'name': '123123',
            'delivery_type': 'other',
        })
        # Create Carrier
        self.delivery_product = self.env['product.product'].create({
            'name': 'Test Carrier1 Delivery',
            'type': 'service',
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Test Carrier1',
            'product_id': self.delivery_product.id,
        })

    def test_delivery_hibou(self):
        # Assign a new shipping account
        self.partner.shipping_account_ids = self.shipping_account

        # Assign values to new Carrier
        test_insurance_value = 600
        test_sig_req_value = 300
        test_procurement_priority = '1'
        self.carrier.automatic_insurance_value = test_insurance_value
        self.carrier.automatic_sig_req_value = test_sig_req_value
        self.carrier.procurement_priority = test_procurement_priority


        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'carrier_id': self.carrier.id,
            'shipping_account_id': self.shipping_account.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
            })]
        })
        sale_order.get_delivery_price()
        sale_order.set_delivery_line()
        sale_order.action_confirm()
        # Make sure 3rd party Shipping Account is set.
        self.assertEqual(sale_order.shipping_account_id, self.shipping_account)

        self.assertTrue(sale_order.picking_ids)
        # Priority coming from Carrier procurement_priority
        self.assertEqual(sale_order.picking_ids.priority, test_procurement_priority)
        # 3rd party Shipping Account copied from Sale Order
        self.assertEqual(sale_order.picking_ids.shipping_account_id, self.shipping_account)
        self.assertEqual(sale_order.carrier_id.get_third_party_account(order=sale_order), self.shipping_account)

        # Test attn
        test_ref = 'TEST100'
        self.assertEqual(sale_order.carrier_id.get_attn(order=sale_order), False)
        sale_order.client_order_ref = test_ref
        self.assertEqual(sale_order.carrier_id.get_attn(order=sale_order), test_ref)
        # The picking should get this ref as well
        self.assertEqual(sale_order.picking_ids.carrier_id.get_attn(picking=sale_order.picking_ids), test_ref)

        # Test order_name
        self.assertEqual(sale_order.carrier_id.get_order_name(order=sale_order), sale_order.name)
        # The picking should get the same 'order_name'
        self.assertEqual(sale_order.picking_ids.carrier_id.get_order_name(picking=sale_order.picking_ids), sale_order.name)

    def test_carrier_hibou_out(self):
        test_insurance_value = 4000
        test_sig_req_value = 4000
        self.carrier.automatic_insurance_value = test_insurance_value
        self.carrier.automatic_sig_req_value = test_sig_req_value

        picking_out = self.env.ref('stock.outgoing_shipment_main_warehouse')
        picking_out.action_assign()
        self.assertEqual(picking_out.state, 'assigned')

        picking_out.carrier_id = self.carrier

        # This relies heavily on the 'stock' demo data.
        # Should only have a single move_line_ids and it should not be done at all.
        self.assertEqual(picking_out.move_line_ids.mapped('qty_done'), [0.0])
        self.assertEqual(picking_out.move_line_ids.mapped('product_uom_qty'), [15.0])
        self.assertEqual(picking_out.move_line_ids.mapped('product_id.standard_price'), [3300.0])

        # The 'value' is assumed to be all of the product value from the initial demand.
        self.assertEqual(picking_out.declared_value(), 15.0 * 3300.0)
        self.assertEqual(picking_out.carrier_id.get_insurance_value(picking=picking_out), picking_out.declared_value())
        self.assertTrue(picking_out.carrier_id.get_signature_required(picking=picking_out))

        # Workflow where user explicitly opts out of insurance on the picking level.
        picking_out.require_insurance = 'no'
        picking_out.require_signature = 'no'
        self.assertEqual(picking_out.carrier_id.get_insurance_value(picking=picking_out), 0.0)
        self.assertFalse(picking_out.carrier_id.get_signature_required(picking=picking_out))
        picking_out.require_insurance = 'auto'
        picking_out.require_signature = 'auto'

        # Lets choose to only delivery one piece at the moment.
        # This does not meet the minimum on the carrier to have insurance value.
        picking_out.move_line_ids.qty_done = 1.0
        self.assertEqual(picking_out.declared_value(), 3300.0)
        self.assertEqual(picking_out.carrier_id.get_insurance_value(picking=picking_out), 0.0)
        self.assertFalse(picking_out.carrier_id.get_signature_required(picking=picking_out))
        # Workflow where user opts in to insurance.
        picking_out.require_insurance = 'yes'
        picking_out.require_signature = 'yes'
        self.assertEqual(picking_out.carrier_id.get_insurance_value(picking=picking_out), 3300.0)
        self.assertTrue(picking_out.carrier_id.get_signature_required(picking=picking_out))
        picking_out.require_insurance = 'auto'
        picking_out.require_signature = 'auto'

        # Test with picking having 3rd party account.
        self.assertEqual(picking_out.carrier_id.get_third_party_account(picking=picking_out), None)
        picking_out.shipping_account_id = self.shipping_account
        self.assertEqual(picking_out.carrier_id.get_third_party_account(picking=picking_out), self.shipping_account)

        # Shipment Time Methods!
        self.assertEqual(picking_out.carrier_id._classify_picking(picking=picking_out), 'out')
        self.assertEqual(picking_out.carrier_id.get_shipper_company(picking=picking_out),
                         picking_out.company_id.partner_id)
        self.assertEqual(picking_out.carrier_id.get_shipper_warehouse(picking=picking_out),
                         picking_out.picking_type_id.warehouse_id.partner_id)
        self.assertEqual(picking_out.carrier_id.get_recipient(picking=picking_out),
                         picking_out.partner_id)
        # This picking has no `sale_id`
        # Right now ATTN requires a sale_id, which this picking doesn't have (none of the stock ones do)
        self.assertEqual(picking_out.carrier_id.get_attn(picking=picking_out), False)
        self.assertEqual(picking_out.carrier_id.get_order_name(picking=picking_out), picking_out.name)

    def test_carrier_hibou_in(self):
        picking_in = self.env.ref('stock.incomming_shipment1')
        self.assertEqual(picking_in.state, 'assigned')

        picking_in.carrier_id = self.carrier
        # This relies heavily on the 'stock' demo data.
        # Should only have a single move_line_ids and it should not be done at all.
        self.assertEqual(picking_in.move_line_ids.mapped('qty_done'), [0.0])
        self.assertEqual(picking_in.move_line_ids.mapped('product_uom_qty'), [35.0])
        self.assertEqual(picking_in.move_line_ids.mapped('product_id.standard_price'), [55.0])

        self.assertEqual(picking_in.carrier_id._classify_picking(picking=picking_in), 'in')
        self.assertEqual(picking_in.carrier_id.get_shipper_company(picking=picking_in),
                         picking_in.company_id.partner_id)
        self.assertEqual(picking_in.carrier_id.get_shipper_warehouse(picking=picking_in),
                         picking_in.partner_id)
        self.assertEqual(picking_in.carrier_id.get_recipient(picking=picking_in),
                         picking_in.picking_type_id.warehouse_id.partner_id)











        







