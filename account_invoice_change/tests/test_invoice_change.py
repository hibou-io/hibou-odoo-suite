from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged, Form
from odoo.addons.account.tests.account_test_users import AccountTestUsers


class InvoiceChangeCommon(AccountTestUsers):
    def setUp(self):
        super().setUp()
        self.account_invoice_obj = self.env['account.move']
        self.payment_term = self.env.ref('account.account_payment_term_advance')
        self.journalrec = self.env['account.journal'].search([('type', '=', 'sale')])[0]
        self.partner3 = self.env.ref('base.res_partner_3')
        self.invoice_basic = self.account_invoice_obj.with_user(self.account_user).create({
            'type': 'out_invoice',
            'name': "Test Customer Invoice",
            'invoice_payment_term_id': self.payment_term.id,
            'journal_id': self.journalrec.id,
            'partner_id': self.partner3.id,
            # account_id=self.account_rec1_id.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.env.ref('product.product_product_5').id,
                'quantity': 10.0,
                'account_id': self.env['account.account'].search(
                    [('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id)], limit=1).id,
                'name': 'product test 5',
                'price_unit': 100.00,
            })],
        })


@tagged('post_install', '-at_install')
class TestInvoiceChange(InvoiceChangeCommon):
    def test_invoice_change_basic(self):
        self.assertEqual(self.invoice_basic.state, 'draft')
        self.invoice_basic.action_post()
        self.assertEqual(self.invoice_basic.state, 'posted')
        self.assertEqual(self.invoice_basic.date, fields.Date.today())
        self.assertEqual(self.invoice_basic.invoice_date, fields.Date.today())
        self.assertEqual(self.invoice_basic.invoice_user_id, self.account_user)
        self.assertEqual(self.invoice_basic.line_ids[0].date, fields.Date.today())

        ctx = {'active_model': 'account.move', 'active_ids': [self.invoice_basic.id]}
        change = self.env['account.invoice.change'].with_context(ctx).create({})
        self.assertEqual(change.date, self.invoice_basic.date)
        self.assertEqual(change.invoice_date, self.invoice_basic.invoice_date)
        self.assertEqual(change.invoice_user_id, self.invoice_basic.invoice_user_id)

        change_date = '2018-01-01'
        change_invoice_date = '2019-01-01'
        change_user = self.env.user
        change.write({'invoice_user_id': change_user.id, 'date': change_date, 'invoice_date': change_invoice_date})

        change.affect_change()
        self.assertEqual(str(self.invoice_basic.date), change_date)
        self.assertEqual(str(self.invoice_basic.invoice_date), change_invoice_date)
        self.assertEqual(self.invoice_basic.invoice_user_id, change_user)
        self.assertEqual(str(self.invoice_basic.line_ids[0].date), change_date)
        
    def _create_journal_entry(self):
        revenue_account = self.env['account.account'].search([
            ('company_id', '=', self.main_company.id),
            ('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id)
        ], limit=1)
        expense_account = self.env['account.account'].search([
            ('company_id', '=', self.main_company.id),
            ('user_type_id', '=', self.env.ref('account.data_account_type_expenses').id)
        ], limit=1)
        return self.env['account.move'].create({
            'type': 'entry',
            'date': '2019-01-01',
            'line_ids': [
                (0, 0, {
                    'name': 'line_debit',
                    'account_id': revenue_account.id,
                }),
                (0, 0, {
                    'name': 'line_credit',
                    'account_id': expense_account.id,
                }),
            ],
        })
        
    def test_invoice_change_multiple(self):
        journal_entry = self._create_journal_entry()
        ctx = {'active_model': 'account.move', 'active_ids': [self.invoice_basic.id, journal_entry.id]}
        with self.assertRaises(UserError):
            change = Form(self.env['account.invoice.change'].with_context(ctx))
            
        other_invoice = self.invoice_basic.copy()
        ctx = {'active_model': 'account.move', 'active_ids': [self.invoice_basic.id, other_invoice.id]}
        with self.assertRaises(UserError):
            change = Form(self.env['account.invoice.change'].with_context(ctx))
        
        self.invoice_basic.action_post()    
        other_invoice.action_post()
        change = Form(self.env['account.invoice.change'].with_context(ctx))
        self.assertFalse(change.date)
        self.assertFalse(change.invoice_date)
        self.assertFalse(change.invoice_user_id)
        
        change_date = '2018-01-01'
        change_invoice_date = '2019-01-01'
        change_user = self.env.user
        change.set_invoice_user_id = True
        change.set_date = True
        change.set_invoice_date = True
        change.invoice_user_id = change_user
        change.date = change_date
        change.invoice_date = change_invoice_date
        
        change.save().affect_change()
        self.assertEqual(str(self.invoice_basic.date), change_date)
        self.assertEqual(str(self.invoice_basic.invoice_date), change_invoice_date)
        self.assertEqual(self.invoice_basic.invoice_user_id, change_user)
        self.assertEqual(str(self.invoice_basic.line_ids[0].date), change_date)
        self.assertEqual(str(other_invoice.date), change_date)
        self.assertEqual(str(other_invoice.invoice_date), change_invoice_date)
        self.assertEqual(other_invoice.invoice_user_id, change_user)
        self.assertEqual(str(other_invoice.line_ids[0].date), change_date)
