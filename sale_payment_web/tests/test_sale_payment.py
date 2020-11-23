from odoo.addons.sale.tests.test_sale_to_invoice import TestSaleToInvoice
from odoo.exceptions import UserError


class TestSalePayment(TestSaleToInvoice):

    def setUp(self):
        super(TestSalePayment, self).setUp()
        self.context = {
            'active_model': 'sale.order',
            'active_ids': [self.sale_order.id],
            'active_id': self.sale_order.id,
        }

    def test_payment(self):
        self.sale_order.action_confirm()

        payment_wizard = self.env['account.payment.register'].with_context(self.context).create({'amount': -15})
        self.assertTrue(payment_wizard.journal_id)
        with self.assertRaises(UserError):
            payment_wizard.create_payments()

        payment_wizard = self.env['account.payment.register'].with_context(self.context).create({'amount': 0})
        self.assertTrue(payment_wizard.journal_id)
        with self.assertRaises(UserError):
            payment_wizard.create_payments()

        payment_wizard = self.env['account.payment.register'].with_context(self.context).create({})
        self.assertTrue(payment_wizard.journal_id)

        payment_action = payment_wizard.create_payments()
        self.assertTrue(isinstance(payment_action, dict))
        payment = self.env[payment_action['res_model']].browse(payment_action['res_id'])
        self.assertTrue(payment.exists())
        self.assertEqual(payment.amount, self.sale_order.amount_total)

        self.assertEqual(payment.sale_order_id, self.sale_order)

        payment_wizard = self.env['account.payment.register'].with_context(self.context).create({'amount': 15})
        self.assertTrue(payment_wizard.journal_id)
        with self.assertRaises(UserError):
            payment_wizard.create_payments()
