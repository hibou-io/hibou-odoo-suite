from odoo.tests.common import TransactionCase


class TestCheckSOExceptions(TransactionCase):
    def setUp(self):
        super(TestCheckSOExceptions, self).setUp()

        self.azure_customer = self.browse_ref('base.res_partner_12')

        self.exception_rule = self.env['exception.rule'].create({
            'name': 'No Azure',
            'description': 'No sales to Azure',
            'active': True,
            'model': 'sale.order',
            'exception_type': 'by_py_code',
            'code': 'failed = sale.partner_id and sale.partner_id.id == %d' % self.azure_customer.id
        })

        self.sale_product = self.browse_ref('product.product_product_5')
        self.sale_product.standard_price = 100.0

    def test_00_check_so_exceptions(self):
        sale_order = self.env['sale.order'].create({
            'partner_id': self.azure_customer.id,
            'order_line': [(0, 0, {
                'product_id': self.sale_product.id,
                'product_uom_qty': 1.0,
                'price_unit': 50.0,  # Set lower than 100.0 to trigger the exception
            })],
        })

        exceptions = sale_order._check_sale_order_exceptions()
        self.assertEqual(len(exceptions), 1)
        self.assertEqual(exceptions[0].get('description'), 'No sales to Azure')

        self.exception_rule.website_description = 'Different message for website'
        exceptions = sale_order._check_sale_order_exceptions()
        self.assertEqual(len(exceptions), 1)
        self.assertEqual(exceptions[0].get('description'), 'Different message for website')

        self.exception_rule.active = False
        exceptions = sale_order._check_sale_order_exceptions()
        self.assertEqual(len(exceptions), 0)
