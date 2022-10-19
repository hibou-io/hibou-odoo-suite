# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from psycopg2.errors import CheckViolation
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests.common import Form
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class PaymentMultiTest(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        # Customer invoices sharing the same batch.
        cls.out_invoice_1 = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'date': '2017-01-01',
            'invoice_date': '2017-01-01',
            'partner_id': cls.partner_a.id,
            'currency_id': cls.currency_data['currency'].id,
            'invoice_line_ids': [(0, 0, {'product_id': cls.product_a.id, 'price_unit': 100.0})],
        })
        cls.out_invoice_2 = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'date': '2017-01-01',
            'invoice_date': '2017-01-01',
            'partner_id': cls.partner_a.id,
            'currency_id': cls.currency_data['currency'].id,
            'invoice_line_ids': [(0, 0, {'product_id': cls.product_a.id, 'price_unit': 500.0})],
        })
        (cls.out_invoice_1 | cls.out_invoice_2).action_post()
        
        # Vendor bills, in_invoice_1 + in_invoice_2 are sharing the same batch but not in_invoice_3.
        cls.in_invoice_1 = cls.env['account.move'].create({
            'move_type': 'in_invoice',
            'date': '2017-01-01',
            'invoice_date': '2017-01-01',
            'partner_id': cls.partner_a.id,
            'invoice_line_ids': [(0, 0, {'product_id': cls.product_a.id, 'price_unit': 100.0})],
        })
        cls.in_invoice_2 = cls.env['account.move'].create({
            'move_type': 'in_invoice',
            'date': '2017-01-01',
            'invoice_date': '2017-01-01',
            'partner_id': cls.partner_a.id,
            'invoice_line_ids': [(0, 0, {'product_id': cls.product_a.id, 'price_unit': 500.0})],
        })
        (cls.in_invoice_1 | cls.in_invoice_2).action_post()
    
    def test_00_disperse_values_currency(self):
        # 500 Gold (invoice) is 1000 Silver (payment) is 250 USD (company)
        platinum = self.setup_multi_currency_data({
            'name': "Silver",
            'symbol': 'S',
            'currency_unit_label': "Silver",
            'currency_subunit_label': "Copper",
        }, rate2017=4.0)['currency']
        payment_register = Form(self.env['account.payment.register'].with_context(active_model='account.move', active_ids=self.out_invoice_2.ids))
        payment_register.currency_id = platinum
        self.assertEqual(payment_register.amount, 1000.0)
        payment_register.is_manual_disperse = True

        with payment_register.payment_invoice_ids.edit(0) as f:
            f.amount = 999.0
        payment_register = payment_register.save()
        disperse_line = payment_register.payment_invoice_ids[0]
        self.assertEqual(disperse_line.residual, 1000.0)
        self.assertEqual(disperse_line.residual_due, 1000.0)
        self.assertEqual(disperse_line.difference, 1.0)
        self.assertEqual(disperse_line.partner_id, self.out_invoice_2.partner_id)
        
    def test_10_multiple_payments_partial(self):
        """ Create test to pay several vendor bills/invoices at once """
        active_ids = (self.out_invoice_1 | self.out_invoice_2).ids
        payment_register = Form(self.env['account.payment.register'].with_context(active_model='account.move', active_ids=active_ids))
        payment_register.is_manual_disperse = True

        with payment_register.payment_invoice_ids.edit(0) as f:
            f.amount = 99.0
        with payment_register.payment_invoice_ids.edit(1) as f:
            f.amount = 300.0

        self.assertEqual(payment_register.amount, 399.0, 'Amount isn\'t the amount from lines')

        # Persist object
        payment_register = payment_register.save()
        payment = payment_register._create_payments()

        self.assertEqual(len(payment), 1, 'Need only one payment.')
        self.assertEqual(payment.amount, 399.0)
        counterpart_lines = payment.line_ids.filtered(lambda l: l.account_id.internal_type in ('receivable', 'payable'))
        self.assertEqual(len(counterpart_lines), 2)
        liquidity_line = payment.line_ids - counterpart_lines
        self.assertEqual(liquidity_line.amount_currency, 399.0)
        self.assertEqual(counterpart_lines[0].amount_currency, -99.0)
        self.assertEqual(counterpart_lines[1].amount_currency, -300.0)

        self.assertEqual(self.out_invoice_1.amount_residual, 1.0)
        self.assertEqual(self.out_invoice_2.amount_residual, 200.0)

        payment_register = Form(self.env['account.payment.register'].with_context(active_model='account.move', active_ids=active_ids))
        payment_register.is_manual_disperse = True

        with payment_register.payment_invoice_ids.edit(0) as f:
            f.amount = 0.0
        with payment_register.payment_invoice_ids.edit(1) as f:
            f.amount = 200.0
        payment_register = payment_register.save()
        payment_register._create_payments()
        self.assertEqual(self.out_invoice_1.amount_residual, 1.0)
        self.assertEqual(self.out_invoice_2.amount_residual, 0.0)

    def test_20_multiple_payments_write_off(self):
        active_ids = (self.out_invoice_1 | self.out_invoice_2).ids
        
        payment_register = Form(self.env['account.payment.register'].with_context(active_model='account.move', active_ids=active_ids))
        payment_register.is_manual_disperse = True
        payment_register.writeoff_account_id = self.company_data['default_account_revenue']

        with payment_register.payment_invoice_ids.edit(0) as f:
            f.amount = 100.0
            f.close_balance = True
        with payment_register.payment_invoice_ids.edit(1) as f:
            f.amount = 300.0
            f.close_balance = True

        self.assertEqual(payment_register.amount, 400.0, 'Amount isn\'t the amount from lines')
        self.assertEqual(payment_register.payment_difference_handling, 'reconcile')

        payment_register = payment_register.save()
        self.assertEqual(sum(payment_register.mapped('payment_invoice_ids.difference')), 200.0)
        self.assertEqual(payment_register.payment_difference_handling, 'reconcile')
        payment = payment_register._create_payments()

        self.assertEqual(len(payment), 1, 'Need only one payment.')
        self.assertEqual(payment.amount, 400.0)

        self.assertEqual(self.out_invoice_1.amount_residual, 0.0)
        self.assertEqual(self.out_invoice_2.amount_residual, 0.0)

    def test_30_vendor_multiple_payments_write_off(self):
        active_ids = (self.in_invoice_1 | self.in_invoice_2).ids
        payment_register = Form(self.env['account.payment.register'].with_context(active_model='account.move', active_ids=active_ids))
        payment_register.is_manual_disperse = True

        with payment_register.payment_invoice_ids.edit(0) as f:
            f.amount = 100.0
        with payment_register.payment_invoice_ids.edit(1) as f:
            f.amount = 300.0

        self.assertEqual(payment_register.amount, 400.0)

        # Cannot have close balance in form because it becomes required
        payment_register = payment_register.save()
        payment_register.action_toggle_close_balance()

        with self.assertRaises(CheckViolation):
            payment_register._create_payments()

        # Need the writeoff account
        payment_register.writeoff_account_id = self.company_data['default_account_revenue']
        payment = payment_register._create_payments()

        self.assertEqual(len(payment), 1, 'Need only one payment.')
        self.assertEqual(payment.amount, 400.0)

        self.assertEqual(self.in_invoice_1.amount_residual, 0.0)
        self.assertEqual(self.in_invoice_2.amount_residual, 0.0)
        
    def test_40_line_is_zero(self):
        active_ids = (self.out_invoice_1 | self.out_invoice_2).ids
        
        payment_register = Form(self.env['account.payment.register'].with_context(active_model='account.move', active_ids=active_ids))
        payment_register.is_manual_disperse = True
        
        with payment_register.payment_invoice_ids.edit(0) as f:
            f.amount = 0.0
        with payment_register.payment_invoice_ids.edit(1) as f:
            f.amount = 300.0

        self.assertEqual(payment_register.amount, 300.0, 'Amount isn\'t the amount from lines')
        self.assertEqual(payment_register.payment_difference_handling, 'open')

        payment_register = payment_register.save()
        self.assertEqual(sum(payment_register.mapped('payment_invoice_ids.difference')), 300.0)
        payment = payment_register._create_payments()

        self.assertEqual(len(payment), 1, 'Need only one payment.')
        counterpart_lines = payment.line_ids.filtered(lambda l: l.account_id.internal_type in ('receivable', 'payable'))
        self.assertEqual(len(counterpart_lines), 1)
        self.assertEqual(payment.amount, 300.0)

        self.assertEqual(self.out_invoice_1.amount_residual, 100.0)
        self.assertEqual(self.out_invoice_2.amount_residual, 200.0)
        
    def test_50_line_is_zero_closed(self):
        active_ids = (self.out_invoice_1 | self.out_invoice_2).ids
        
        payment_register = Form(self.env['account.payment.register'].with_context(active_model='account.move', active_ids=active_ids))
        payment_register.is_manual_disperse = True
        payment_register.writeoff_account_id = self.company_data['default_account_revenue']
        
        with payment_register.payment_invoice_ids.edit(0) as f:
            f.amount = 0.0
            f.close_balance = True
        with payment_register.payment_invoice_ids.edit(1) as f:
            f.amount = 300.0

        self.assertEqual(payment_register.amount, 300.0, 'Amount isn\'t the amount from lines')
        self.assertEqual(payment_register.payment_difference_handling, 'reconcile')

        payment_register = payment_register.save()
        self.assertEqual(sum(payment_register.mapped('payment_invoice_ids.difference')), 300.0)
        payment = payment_register._create_payments()

        self.assertEqual(len(payment), 1, 'Need only one payment.')
        counterpart_lines = payment.line_ids.filtered(lambda l: l.account_id.internal_type in ('receivable', 'payable'))
        self.assertEqual(len(counterpart_lines), 2)
        self.assertEqual(payment.amount, 300.0)

        self.assertEqual(self.out_invoice_1.amount_residual, 0.0)
        self.assertEqual(self.out_invoice_2.amount_residual, 200.0)
