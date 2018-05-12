from odoo.addons.account.tests.account_test_users import AccountTestUsers
from odoo import fields

class TestInvoiceChange(AccountTestUsers):

    def test_invoice_change_basic(self):
        self.account_invoice_obj = self.env['account.invoice']
        self.payment_term = self.env.ref('account.account_payment_term_advance')
        self.journalrec = self.env['account.journal'].search([('type', '=', 'sale')])[0]
        self.partner3 = self.env.ref('base.res_partner_3')
        account_user_type = self.env.ref('account.data_account_type_receivable')
        self.account_rec1_id = self.account_model.sudo(self.account_manager.id).create(dict(
            code="cust_acc",
            name="customer account",
            user_type_id=account_user_type.id,
            reconcile=True,
        ))
        invoice_line_data = [
            (0, 0,
             {
                 'product_id': self.env.ref('product.product_product_5').id,
                 'quantity': 10.0,
                 'account_id': self.env['account.account'].search(
                     [('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id)], limit=1).id,
                 'name': 'product test 5',
                 'price_unit': 100.00,
             }
             )
        ]
        self.invoice_basic = self.account_invoice_obj.sudo(self.account_user.id).create(dict(
            name="Test Customer Invoice",
            reference_type="none",
            payment_term_id=self.payment_term.id,
            journal_id=self.journalrec.id,
            partner_id=self.partner3.id,
            account_id=self.account_rec1_id.id,
            invoice_line_ids=invoice_line_data
        ))
        self.assertEqual(self.invoice_basic.state, 'draft')
        self.invoice_basic.action_invoice_open()
        self.assertEqual(self.invoice_basic.state, 'open')
        self.assertEqual(self.invoice_basic.date, fields.Date.today())
        self.assertEqual(self.invoice_basic.user_id, self.account_user)
        self.assertEqual(self.invoice_basic.move_id.date, fields.Date.today())
        self.assertEqual(self.invoice_basic.move_id.line_ids[0].date, fields.Date.today())

        ctx = {'active_model': 'account.invoice', 'active_ids': [self.invoice_basic.id]}
        change = self.env['account.invoice.change'].with_context(ctx).create({})
        self.assertEqual(change.date, self.invoice_basic.date)
        self.assertEqual(change.user_id, self.invoice_basic.user_id)

        change_date = '2018-01-01'
        change_user = self.env.user
        change.write({'user_id': change_user.id, 'date': change_date})

        change.affect_change()
        self.assertEqual(self.invoice_basic.date, change_date)
        self.assertEqual(self.invoice_basic.user_id, change_user)
        self.assertEqual(self.invoice_basic.move_id.date, change_date)
        self.assertEqual(self.invoice_basic.move_id.line_ids[0].date, change_date)
