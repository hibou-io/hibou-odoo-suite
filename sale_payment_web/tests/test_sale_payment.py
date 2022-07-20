from odoo.addons.sale.tests.test_sale_to_invoice import TestSaleToInvoice
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestSalePayment(TestSaleToInvoice):

    def _sale_context(self):
        return {
            'active_model': 'sale.order',
            'active_ids': [self.sale_order.id],
            'active_id': self.sale_order.id,
        }

    def test_00_payment(self):
        self.sale_order.action_confirm()

        payment_wizard = self.env['account.payment.register'].with_context(self._sale_context()).create({'amount': -15})
        self.assertTrue(payment_wizard.journal_id)
        with self.assertRaises(UserError):
            payment_wizard._create_payments()

        payment_wizard = self.env['account.payment.register'].with_context(self._sale_context()).create({'amount': 0})
        self.assertTrue(payment_wizard.journal_id)
        with self.assertRaises(UserError):
            payment_wizard._create_payments()

        payment_wizard = self.env['account.payment.register'].with_context(self._sale_context()).create({})
        self.assertTrue(payment_wizard.journal_id)

        payment = payment_wizard._create_payments()
        self.assertEqual(payment.amount, self.sale_order.amount_total)
        self.assertEqual(payment.sale_order_id, self.sale_order)
        self.assertEqual(self.sale_order.manual_amount_remaining, 0.0)

        payment_wizard = self.env['account.payment.register'].with_context(self._sale_context()).create({'amount': 15})
        self.assertTrue(payment_wizard.journal_id)
        with self.assertRaises(UserError):
            payment_wizard._create_payments()
            
    def test_10_partial_payment(self):
        payment_wizard = self.env['account.payment.register'].with_context(self._sale_context()).create({'amount': 50})
        self.assertTrue(payment_wizard.journal_id)

        payment = payment_wizard._create_payments()
        self.assertEqual(payment.amount, 50)
        self.assertEqual(payment.sale_order_id, self.sale_order)
        self.assertEqual(self.sale_order.manual_amount_remaining, self.sale_order.amount_total - 50)
