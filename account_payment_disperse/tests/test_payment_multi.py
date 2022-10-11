# from odoo.addons.account.tests.test_payment import TestPayment
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
import time


# class PaymentMultiTest(TestPayment):
class PaymentMultiTest(TransactionCase):

    # @classmethod
    def setUp(self):
        super().setUp()
        self.register_payments_model = self.env['account.payment.register'].with_context(active_model='account.move')
        self.payment_model = self.env['account.payment']
        self.invoice_model = self.env['account.move']
        self.invoice_line_model = self.env['account.move.line']

        self.partner_agrolait = self.env.ref("base.res_partner_2")
        self.partner_china_exp = self.env.ref("base.res_partner_3")
        self.currency_eur_id = self.env.ref("base.EUR").id

        self.product = self.env.ref("product.product_product_4")
        self.payment_method_manual_in = self.env.ref("account.account_payment_method_manual_in")
        self.payment_method_manual_out = self.env.ref("account.account_payment_method_manual_out")

        self.account_receivable = self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_account_type_receivable').id)], limit=1)
        self.account_revenue = self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id)], limit=1)

        self.bank_journal_euro = self.env['account.journal'].create({'name': 'Bank', 'type': 'bank', 'code': 'BNK67'})        

    def create_invoice(self, amount=100, move_type='out_invoice', currency_id=None, partner=None, account_id=None):
        """ Returns an open invoice """
        invoice = self.invoice_model.create({
            'partner_id': partner or self.partner_agrolait.id,
            'currency_id': currency_id or self.currency_eur_id,
            # 'name': move_type,
            'account_id': account_id or self.account_receivable.id,
            'move_type': move_type,
            'invoice_date': time.strftime('%Y') + '-06-26',
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 1.0,
                    'price_unit': amount,
                    # 'move_id': invoice.id,
                    'name': 'something',
                    'account_id': self.account_revenue.id,
                }),
            ],
        })
        invoice.action_post()
        return invoice

    def test_multiple_payments_partial(self):
        """ Create test to pay several vendor bills/invoices at once """
        # One payment for inv_1 and inv_2 (same partner)
        inv_1 = self.create_invoice(amount=100, currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)
        inv_2 = self.create_invoice(amount=500, currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)

        ids = [inv_1.id, inv_2.id]
        register_payments = self.register_payments_model.with_context(active_ids=ids).create({
            'payment_date': time.strftime('%Y') + '-07-15',
            'journal_id': self.bank_journal_euro.id,
            'payment_method_line_id': self.payment_method_manual_in.id,
        })
        register_payments.amount = 399.0
        register_payments.is_manual_disperse = True

        with self.assertRaises(ValidationError):
            register_payments._create_payments()

        for line in register_payments.invoice_line_ids:
            if line.move_id == inv_1:
                line.amount = 99.0
            if line.move_id == inv_2:
                line.amount = 300.0

        register_payments._create_payments()

    #     payment_ids = self.payment_model.search([('move_ids', 'in', ids)], order="id desc")
    #     self.assertEqual(len(payment_ids), 1, 'Need only one payment.')
    #     self.assertEqual(payment_ids.amount, 399.0)

    #     self.assertEqual(inv_1.residual_signed, 1.0)
    #     self.assertEqual(inv_2.residual_signed, 200.0)

    #     register_payments = self.register_payments_model.with_context(active_ids=ids).create({
    #         'payment_date': time.strftime('%Y') + '-07-15',
    #         'journal_id': self.bank_journal_euro.id,
    #         'payment_method_id': self.payment_method_manual_in.id,
    #     })
    #     register_payments.amount = 200.0
    #     register_payments.is_manual_disperse = True

    #     for line in register_payments.invoice_line_ids:
    #         if line.move_id == inv_2:
    #             line.amount = 200.0

    #     register_payments._create_payments()
    #     self.assertEqual(inv_1.residual_signed, 1.0)
    #     self.assertEqual(inv_2.residual_signed, 0.0)

    # def test_multiple_payments_write_off(self):
    #     inv_1 = self.create_invoice(amount=100, currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)
    #     inv_2 = self.create_invoice(amount=500, currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)

    #     ids = [inv_1.id, inv_2.id]
    #     register_payments = self.register_payments_model.with_context(active_ids=ids).create({
    #         'payment_date': time.strftime('%Y') + '-07-15',
    #         'journal_id': self.bank_journal_euro.id,
    #         'payment_method_id': self.payment_method_manual_in.id,
    #     })
    #     register_payments.amount = 400.0
    #     register_payments.is_manual_disperse = True
    #     register_payments.writeoff_journal_id = inv_1.journal_id

    #     with self.assertRaises(ValidationError):
    #         register_payments._create_payments()

    #     for line in register_payments.invoice_line_ids:
    #         if line.move_id == inv_1:
    #             line.amount = 100.0
    #         if line.move_id == inv_2:
    #             line.amount = 300.0
    #             line.writeoff_acc_id = self.account_revenue

    #     register_payments._create_payments()

    #     payment_ids = self.payment_model.search([('move_ids', 'in', ids)], order="id desc")
    #     self.assertEqual(len(payment_ids), 1, 'Need only one payment.')
    #     self.assertEqual(payment_ids.amount, 400.0)

    #     self.assertEqual(inv_1.residual_signed, 0.0)
    #     self.assertEqual(inv_2.residual_signed, 0.0)

    # def test_multiple_payments_partial_multi(self):
    #     """ Create test to pay several vendor bills/invoices at once """
    #     # One payment for inv_1 and inv_2 (same partner)
    #     inv_1 = self.create_invoice(amount=100, currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)
    #     inv_2 = self.create_invoice(amount=500, currency_id=self.currency_eur_id, partner=self.partner_china_exp.id)

    #     ids = [inv_1.id, inv_2.id]
    #     register_payments = self.register_payments_model.with_context(active_ids=ids).create({
    #         'payment_date': time.strftime('%Y') + '-07-15',
    #         'journal_id': self.bank_journal_euro.id,
    #         'payment_method_id': self.payment_method_manual_in.id,
    #     })
    #     register_payments.amount = 400.0
    #     register_payments.is_manual_disperse = True

    #     for line in register_payments.invoice_line_ids:
    #         if line.move_id == inv_1:
    #             line.amount = 100.0
    #         if line.move_id == inv_2:
    #             line.amount = 300.0

    #     register_payments._create_payments()

    #     payment_ids = self.payment_model.search([('move_ids', 'in', ids)], order="id desc")
    #     self.assertEqual(len(payment_ids), 2, 'Need two payments.')
    #     # Useful for logging amounts of payments and their accounting
    #     # for pay in payment_ids:
    #     #     _logger.warn(str(pay) + ' amount: ' + str(pay.amount))
    #     #     for line in pay.move_line_ids:
    #     #         _logger.warn('  ' +
    #     #                      str(line) + ' name: ' + str(line.name) + ' :: credit: ' + str(line.credit) + ' debit: ' +
    #     #                      str(line.debit))
    #     self.assertEqual(sum(payment_ids.mapped('amount')), 400.0)

    #     self.assertEqual(inv_1.residual_signed, 0.0)
    #     self.assertEqual(inv_2.residual_signed, 200.0)

    # def test_vendor_multiple_payments_write_off(self):
    #     inv_1 = self.create_invoice(amount=100, move_type='in_invoice', currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)
    #     inv_2 = self.create_invoice(amount=500, move_type='in_invoice', currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)
    #     ids = [inv_1.id, inv_2.id]
    #     register_payments = self.register_payments_model.with_context(active_ids=ids).create({
    #         'payment_date': time.strftime('%Y') + '-07-15',
    #         'journal_id': self.bank_journal_euro.id,
    #         'payment_method_id': self.payment_method_manual_out.id,
    #     })
    #     register_payments.amount = 400.0
    #     register_payments.is_manual_disperse = True
    #     register_payments.writeoff_journal_id = inv_1.journal_id

    #     with self.assertRaises(ValidationError):
    #         register_payments._create_payments()

    #     for line in register_payments.invoice_line_ids:
    #         if line.move_id == inv_1:
    #             line.amount = 100.0
    #         if line.move_id == inv_2:
    #             line.amount = 300.0
    #             line.writeoff_acc_id = self.account_revenue

    #     register_payments._create_payments()

    #     payment_ids = self.payment_model.search([('move_ids', 'in', ids)], order="id desc")
    #     self.assertEqual(len(payment_ids), 1, 'Need only one payment.')
    #     self.assertEqual(payment_ids.amount, 400.0)

    #     self.assertEqual(inv_1.residual_signed, 0.0)
    #     self.assertEqual(inv_2.residual_signed, 0.0)
