# © 2021 Hibou Corp.

from .api.orders import mock_orders_api
from .common import AmazonTestCase


class TestSaleOrder(AmazonTestCase):

    def _import_sale_order(self, amazon_id):
        with mock_orders_api():
            return self._import_record('amazon.sale.order', amazon_id)

    def test_import_sale_order(self):
        """ Import sale order and test workflow"""
        amazon_order_number = '111-1111111-1111111'
        binding = self._import_sale_order(amazon_order_number)
        # binding.external_id will be what we pass to import_record regardless of what the API returned
        self.assertEqual(binding.external_id, amazon_order_number)
        self.assertTrue(binding.is_amazon_order)
        self.assertFalse(binding.odoo_id.is_amazon_order)
        self.assertEqual(binding.effective_date, False)  # This is a computed field, should it be in the mapper?
        self.assertEqual(binding.date_planned, '2021-04-27 06:59:59')
        self.assertEqual(binding.requested_date, '2021-05-01 06:59:59')
        self.assertEqual(binding.ship_service_level, 'Std US D2D Dom')
        self.assertEqual(binding.ship_service_level_category, 'Standard')
        self.assertEqual(binding.marketplace, 'ATVPDKIKX0DER')
        self.assertEqual(binding.order_type, 'StandardOrder')
        self.assertFalse(binding.is_business_order)
        self.assertTrue(binding.is_prime)
        self.assertFalse(binding.is_global_express_enabled)
        self.assertFalse(binding.is_premium)
        self.assertFalse(binding.is_sold_by_ab)
        self.assertEqual(binding.name, 'TEST' + amazon_order_number)
        self.assertAlmostEqual(binding.total_amount, 159.96)
        self.assertEqual(binding.currency_id, self.browse_ref('base.USD'))
        default_warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)], limit=1)
        self.assertEqual(binding.warehouse_id, default_warehouse)
        self.assertEqual(binding.payment_mode_id, self.browse_ref('account_payment_mode.payment_mode_inbound_ct1'))

        self.assertEqual(len(binding.amazon_order_line_ids), 1)
        self._test_import_sale_order_line(binding.amazon_order_line_ids[0])

        self.assertEqual(binding.state, 'draft')
        binding.action_confirm()
        self.assertEqual(binding.state, 'sale')
        self.assertEqual(binding.delivery_count, 1)

        binding.action_cancel()
        self.assertEqual(binding.state, 'cancel')

        binding.action_draft()
        self.assertEqual(binding.state, 'draft')

    def _test_import_sale_order_line(self, binding_line):
        self.assertEqual(binding_line.external_id, '12345678901234')
        self.assertEqual(binding_line.name, 'Test Product Purchased From Amazon')
        self.assertEqual(binding_line.product_uom_qty, 1)
        self.assertAlmostEqual(binding_line.price_unit, 199.95)
        self.assertAlmostEqual(binding_line.discount, 20.0)
        product = binding_line.product_id
        self.assertEqual(product.default_code, 'TEST_PRODUCT')
        self.assertEqual(product.name, 'Test Product Purchased From Amazon')
        self.assertAlmostEqual(product.list_price, 199.95)
        self.assertEqual(product.categ_id, self.browse_ref('product.product_category_1'))
        product_binding = product.amazon_bind_ids[0]
        self.assertEqual(product_binding.external_id, product.default_code)
        self.assertEqual(product_binding.asin, 'A1B1C1D1E1')
