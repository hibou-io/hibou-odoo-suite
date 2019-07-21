from odoo.addons.account.tests.test_payment import TestPayment
from odoo.exceptions import ValidationError
import time


class PaymentMultiTest(TestPayment):
    
    def test_multiple_payments_partial(self):
        """ Create test to pay several vendor bills/invoices at once """
        # One payment for inv_1 and inv_2 (same partner)
        inv_1 = self.create_invoice(amount=100, currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)
        inv_2 = self.create_invoice(amount=500, currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)

        ids = [inv_1.id, inv_2.id]
        register_payments = self.register_payments_model.with_context(active_ids=ids).create({
            'payment_date': time.strftime('%Y') + '-07-15',
            'journal_id': self.bank_journal_euro.id,
            'payment_method_id': self.payment_method_manual_in.id,
        })
        register_payments.amount = 399.0
        register_payments.is_manual_disperse = True

        with self.assertRaises(ValidationError):
            register_payments.create_payments()

        for line in register_payments.invoice_line_ids:
            if line.invoice_id == inv_1:
                line.amount = 99.0
            if line.invoice_id == inv_2:
                line.amount = 300.0

        register_payments.create_payments()

        payment_ids = self.payment_model.search([('invoice_ids', 'in', ids)], order="id desc")
        self.assertEqual(len(payment_ids), 1, 'Need only one payment.')
        self.assertEqual(payment_ids.amount, 399.0)

        self.assertEqual(inv_1.residual_signed, 1.0)
        self.assertEqual(inv_2.residual_signed, 200.0)

        register_payments = self.register_payments_model.with_context(active_ids=ids).create({
            'payment_date': time.strftime('%Y') + '-07-15',
            'journal_id': self.bank_journal_euro.id,
            'payment_method_id': self.payment_method_manual_in.id,
        })
        register_payments.amount = 200.0
        register_payments.is_manual_disperse = True

        for line in register_payments.invoice_line_ids:
            if line.invoice_id == inv_2:
                line.amount = 200.0

        register_payments.create_payments()
        self.assertEqual(inv_1.residual_signed, 1.0)
        self.assertEqual(inv_2.residual_signed, 0.0)

    def test_multiple_payments_write_off(self):
        inv_1 = self.create_invoice(amount=100, currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)
        inv_2 = self.create_invoice(amount=500, currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)

        ids = [inv_1.id, inv_2.id]
        register_payments = self.register_payments_model.with_context(active_ids=ids).create({
            'payment_date': time.strftime('%Y') + '-07-15',
            'journal_id': self.bank_journal_euro.id,
            'payment_method_id': self.payment_method_manual_in.id,
        })
        register_payments.amount = 400.0
        register_payments.is_manual_disperse = True
        register_payments.writeoff_journal_id = inv_1.journal_id

        with self.assertRaises(ValidationError):
            register_payments.create_payments()

        for line in register_payments.invoice_line_ids:
            if line.invoice_id == inv_1:
                line.amount = 100.0
            if line.invoice_id == inv_2:
                line.amount = 300.0
                line.writeoff_acc_id = self.account_revenue

        register_payments.create_payments()

        payment_ids = self.payment_model.search([('invoice_ids', 'in', ids)], order="id desc")
        self.assertEqual(len(payment_ids), 1, 'Need only one payment.')
        self.assertEqual(payment_ids.amount, 400.0)

        self.assertEqual(inv_1.residual_signed, 0.0)
        self.assertEqual(inv_2.residual_signed, 0.0)

    def test_multiple_payments_partial_multi(self):
        """ Create test to pay several vendor bills/invoices at once """
        # One payment for inv_1 and inv_2 (same partner)
        inv_1 = self.create_invoice(amount=100, currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)
        inv_2 = self.create_invoice(amount=500, currency_id=self.currency_eur_id, partner=self.partner_china_exp.id)

        ids = [inv_1.id, inv_2.id]
        register_payments = self.register_payments_model.with_context(active_ids=ids).create({
            'payment_date': time.strftime('%Y') + '-07-15',
            'journal_id': self.bank_journal_euro.id,
            'payment_method_id': self.payment_method_manual_in.id,
        })
        register_payments.amount = 400.0
        register_payments.is_manual_disperse = True

        for line in register_payments.invoice_line_ids:
            if line.invoice_id == inv_1:
                line.amount = 100.0
            if line.invoice_id == inv_2:
                line.amount = 300.0

        register_payments.create_payments()

        payment_ids = self.payment_model.search([('invoice_ids', 'in', ids)], order="id desc")
        self.assertEqual(len(payment_ids), 2, 'Need two payments.')
        # Useful for logging amounts of payments and their accounting
        # for pay in payment_ids:
        #     _logger.warn(str(pay) + ' amount: ' + str(pay.amount))
        #     for line in pay.move_line_ids:
        #         _logger.warn('  ' +
        #                      str(line) + ' name: ' + str(line.name) + ' :: credit: ' + str(line.credit) + ' debit: ' +
        #                      str(line.debit))
        self.assertEqual(sum(payment_ids.mapped('amount')), 400.0)

        self.assertEqual(inv_1.residual_signed, 0.0)
        self.assertEqual(inv_2.residual_signed, 200.0)

    def test_vendor_multiple_payments_write_off(self):
        inv_1 = self.create_invoice(amount=100, type='in_invoice', currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)
        inv_2 = self.create_invoice(amount=500, type='in_invoice', currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)
        ids = [inv_1.id, inv_2.id]
        register_payments = self.register_payments_model.with_context(active_ids=ids).create({
            'payment_date': time.strftime('%Y') + '-07-15',
            'journal_id': self.bank_journal_euro.id,
            'payment_method_id': self.payment_method_manual_out.id,
        })
        register_payments.amount = 400.0
        register_payments.is_manual_disperse = True
        register_payments.writeoff_journal_id = inv_1.journal_id

        with self.assertRaises(ValidationError):
            register_payments.create_payments()

        for line in register_payments.invoice_line_ids:
            if line.invoice_id == inv_1:
                line.amount = 100.0
            if line.invoice_id == inv_2:
                line.amount = 300.0
                line.writeoff_acc_id = self.account_revenue

        register_payments.create_payments()

        payment_ids = self.payment_model.search([('invoice_ids', 'in', ids)], order="id desc")
        self.assertEqual(len(payment_ids), 1, 'Need only one payment.')
        self.assertEqual(payment_ids.amount, 400.0)

        self.assertEqual(inv_1.residual_signed, 0.0)
        self.assertEqual(inv_2.residual_signed, 0.0)
