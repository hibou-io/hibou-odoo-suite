# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo.addons.account.tests.test_payment import TestPayment
from odoo.tests.common import Form
from odoo.tests import tagged
from odoo.exceptions import ValidationError
import time


# Fun fact... if you install enterprise accounting, you'll get errors
# due to required fields being missing...
# The classic fix would be the following @tagged, but for some reason this makes
# odoo.tests.common.Form suddenly not calculate the amount on the register payment wizard
# @tagged('post_install', '-at_install')
class PaymentMultiTest(TestPayment):
    
    def test_multiple_payments_partial(self):
        """ Create test to pay several vendor bills/invoices at once """
        # One payment for inv_1 and inv_2 (same partner)
        inv_1 = self.create_invoice(amount=100, currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)
        inv_2 = self.create_invoice(amount=500, currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)

        ids = [inv_1.id, inv_2.id]
        payment_register = Form(self.register_payments_model.with_context(active_ids=ids))
        payment_register.journal_id = self.bank_journal_euro
        payment_register.payment_date = time.strftime('%Y') + '-07-15'
        payment_register.is_manual_disperse = True

        with payment_register.payment_invoice_ids.edit(0) as f:
            f.amount = 99.0
            f.save()
        with payment_register.payment_invoice_ids.edit(1) as f:
            f.amount = 300.0
            f.save()

        self.assertEqual(payment_register.amount, 399.0, 'Amount isn\'t the amount from lines')

        # Persist object
        payment_register = payment_register.save()
        payment_register.create_payments()

        payment_ids = self.payment_model.search([('invoice_ids', 'in', ids)], order="id desc")
        self.assertEqual(len(payment_ids), 1, 'Need only one payment.')
        self.assertEqual(payment_ids.amount, 399.0)

        self.assertEqual(inv_1.amount_residual_signed, 1.0)
        self.assertEqual(inv_2.amount_residual_signed, 200.0)

        payment_register = Form(self.register_payments_model.with_context(active_ids=ids))
        payment_register.journal_id = self.bank_journal_euro
        payment_register.payment_date = time.strftime('%Y') + '-07-15'
        payment_register.is_manual_disperse = True

        with payment_register.payment_invoice_ids.edit(0) as f:
            f.amount = 0.0
            f.save()
        with payment_register.payment_invoice_ids.edit(1) as f:
            f.amount = 200.0
            f.save()
        payment_register = payment_register.save()
        payment_register.create_payments()
        self.assertEqual(inv_1.amount_residual_signed, 1.0)
        self.assertEqual(inv_2.amount_residual_signed, 0.0)

    def test_multiple_payments_write_off(self):
        inv_1 = self.create_invoice(amount=100, currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)
        inv_2 = self.create_invoice(amount=500, currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)

        ids = [inv_1.id, inv_2.id]
        payment_register = Form(self.register_payments_model.with_context(active_ids=ids))
        payment_register.journal_id = self.bank_journal_euro
        payment_register.payment_date = time.strftime('%Y') + '-07-15'
        payment_register.is_manual_disperse = True
        payment_register.writeoff_account_id = self.transfer_account

        with payment_register.payment_invoice_ids.edit(0) as f:
            f.amount = 100.0
            f.close_balance = True
            f.save()
        with payment_register.payment_invoice_ids.edit(1) as f:
            f.amount = 300.0
            f.close_balance = True
            f.save()

        self.assertEqual(payment_register.amount, 400.0, 'Amount isn\'t the amount from lines')

        payment_register = payment_register.save()
        self.assertEqual(sum(payment_register.mapped('payment_invoice_ids.difference')), -200.0)
        payment_register.create_payments()

        payment_ids = self.payment_model.search([('invoice_ids', 'in', ids)], order="id desc")
        self.assertEqual(len(payment_ids), 1, 'Need only one payment.')
        self.assertEqual(payment_ids.amount, 400.0)

        self.assertEqual(inv_1.amount_residual_signed, 0.0)
        self.assertEqual(inv_2.amount_residual_signed, 0.0)

    def test_multiple_payments_partial_multi(self):
        """ Create test to pay several vendor bills/invoices at once """
        # One payment for inv_1 and inv_2 (different partners)
        inv_1 = self.create_invoice(amount=100, currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)
        inv_2 = self.create_invoice(amount=500, currency_id=self.currency_eur_id, partner=self.partner_china_exp.id)

        ids = [inv_1.id, inv_2.id]
        payment_register = Form(self.register_payments_model.with_context(active_ids=ids))
        payment_register.journal_id = self.bank_journal_euro
        payment_register.payment_date = time.strftime('%Y') + '-07-15'
        payment_register.is_manual_disperse = True

        with payment_register.payment_invoice_ids.edit(0) as f:
            f.amount = 100.0
            f.save()
        with payment_register.payment_invoice_ids.edit(1) as f:
            f.amount = 300.0
            f.save()

        self.assertEqual(payment_register.amount, 400.0, 'Amount isn\'t the amount from lines')

        payment_register = payment_register.save()
        payment_register.create_payments()

        payment_ids = self.payment_model.search([('invoice_ids', 'in', ids)], order="id desc")
        self.assertEqual(len(payment_ids), 2, 'Need two payments.')
        self.assertEqual(sum(payment_ids.mapped('amount')), 400.0)

        self.assertEqual(inv_1.amount_residual_signed, 0.0)
        self.assertEqual(inv_2.amount_residual_signed, 200.0)

    def test_vendor_multiple_payments_write_off(self):
        inv_1 = self.create_invoice(amount=100, type='in_invoice', currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)
        inv_2 = self.create_invoice(amount=500, type='in_invoice', currency_id=self.currency_eur_id, partner=self.partner_agrolait.id)
        ids = [inv_1.id, inv_2.id]
        payment_register = Form(self.register_payments_model.with_context(active_ids=ids))
        payment_register.journal_id = self.bank_journal_euro
        payment_register.payment_date = time.strftime('%Y') + '-07-15'
        payment_register.is_manual_disperse = True

        with payment_register.payment_invoice_ids.edit(0) as f:
            f.amount = 100.0
            f.save()
        with payment_register.payment_invoice_ids.edit(1) as f:
            f.amount = 300.0
            f.save()

        self.assertEqual(payment_register.amount, 400.0)

        # Cannot have close balance in form because it becomes required
        payment_register = payment_register.save()
        payment_register.action_toggle_close_balance()

        with self.assertRaises(ValidationError):
            payment_register.create_payments()

        # Need the writeoff account
        payment_register.writeoff_account_id = self.transfer_account
        payment_register.create_payments()

        payment_ids = self.payment_model.search([('invoice_ids', 'in', ids)], order="id desc")
        self.assertEqual(len(payment_ids), 1, 'Need only one payment.')
        self.assertEqual(payment_ids.amount, 400.0)

        self.assertEqual(inv_1.amount_residual_signed, 0.0)
        self.assertEqual(inv_2.amount_residual_signed, 0.0)
