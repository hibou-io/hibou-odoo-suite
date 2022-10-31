from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
from odoo import fields
from odoo import Command


@tagged('post_install', '-at_install')
class TestInvoiceChange(AccountTestInvoicingCommon):

    def test_invoice_change_basic(self):
        self.account_invoice_obj = self.env['account.move']
        self.payment_term = self.env.ref('account.account_payment_term_advance')
        self.journalrec = self.env['account.journal'].search([('type', '=', 'sale')])[0]
        self.partner3 = self.env.ref('base.res_partner_3')
        self.invoice_basic = self.env['account.move'].create([{
            'move_type': 'out_invoice',
            'name': "Test Customer Invoice",
            'invoice_payment_term_id': self.payment_term.id,
            'journal_id': self.journalrec.id,
            'partner_id': self.partner3.id,
            'line_ids':[Command.create({
                'product_id': self.product_a.id,
                'quantity': 10.0,
                'price_unit': 100.00,
            })],
        }])
        self.assertEqual(self.invoice_basic.state, 'draft')
        self.invoice_basic.action_post()
        self.assertEqual(self.invoice_basic.state, 'posted')
        self.assertEqual(self.invoice_basic.date, fields.Date.today())
        self.assertEqual(self.invoice_basic.invoice_date, fields.Date.today())
        # self.assertEqual(self.invoice_basic.invoice_user_id, self.account_user)
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
