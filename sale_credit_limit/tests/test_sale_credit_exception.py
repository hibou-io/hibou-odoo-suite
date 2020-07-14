
from odoo.addons.sale_exception.tests.test_sale_exception import TestSaleException


class TestSaleCreditException(TestSaleException):

    def setUp(self):
        super(TestSaleCreditException, self).setUp()

    def test_sale_order_credit_limit_exception(self):
        self.sale_exception_confirm = self.env['sale.exception.confirm']
        exception = self.env.ref('sale_credit_limit.excep_sale_credit_limit')
        exception.active = True
        partner = self.env.ref('base.res_partner_12')
        partner.credit_limit = 100.00
        p = self.env.ref('product.product_product_25_product_template')
        so1 = self.env['sale.order'].create({
            'partner_id': partner.id,
            'partner_invoice_id': partner.id,
            'partner_shipping_id': partner.id,
            'order_line': [(0, 0, {'name': p.name,
                                   'product_id': p.id,
                                   'product_uom_qty': 2,
                                   'product_uom': p.uom_id.id,
                                   'price_unit': p.list_price})],
            'pricelist_id': self.env.ref('product.list0').id,
        })

        # confirm quotation
        so1.action_confirm()
        self.assertTrue(so1.state == 'draft')
        self.assertFalse(so1.ignore_exception)
