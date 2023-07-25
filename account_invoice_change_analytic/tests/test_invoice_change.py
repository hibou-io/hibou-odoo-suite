from odoo.addons.account_invoice_change.tests.test_invoice_change import TestInvoiceChange


class TestWizard(TestInvoiceChange):
    def test_invoice_change_basic(self):
        self.analytic_account = self.env['account.analytic.account'].create({
            'name': 'test account',
        })
        self.analytic_account2 = self.env['account.analytic.account'].create({
            'name': 'test account2',
        })

        super(TestWizard, self).test_invoice_change_basic()
        # Tests Adding an Analytic Account
        self.assertFalse(self.invoice_basic.line_ids.mapped('analytic_account_id'))
        ctx = {'active_model': 'account.move', 'active_ids': [self.invoice_basic.id]}
        change = self.env['account.invoice.change'].with_context(ctx).create({})
        change.analytic_account_id = self.analytic_account
        change.affect_change()
        # Do not want to set analytic account on receivable lines
        invoice_lines = self.invoice_basic.invoice_line_ids
        other_lines = self.invoice_basic.line_ids - invoice_lines
        self.assertEqual(invoice_lines.analytic_account_id, self.analytic_account)
        self.assertFalse(other_lines.analytic_account_id)
        self.assertEqual(invoice_lines.analytic_line_ids.account_id, self.analytic_account)

        # Tests Removing Analytic Account
        new_invoice = self.invoice_basic.copy()
        new_invoice.invoice_line_ids.analytic_account_id = self.analytic_account
        new_invoice.action_post()
        self.assertEqual(new_invoice.state, 'posted')
        self.assertEqual(new_invoice.mapped('line_ids.analytic_account_id'), self.analytic_account)
        ctx = {'active_model': 'account.move', 'active_ids': [new_invoice.id]}
        change = self.env['account.invoice.change'].with_context(ctx).create({})
        change.analytic_account_id = False
        change.affect_change()
        invoice_lines = new_invoice.invoice_line_ids
        other_lines = new_invoice.line_ids - invoice_lines
        self.assertFalse(invoice_lines.analytic_account_id)
        self.assertFalse(other_lines.analytic_account_id)
        self.assertFalse(invoice_lines.analytic_line_ids)

        # Tests Changing Analytic Account
        new_invoice = self.invoice_basic.copy()
        new_invoice.invoice_line_ids.analytic_account_id = self.analytic_account
        new_invoice.action_post()
        self.assertEqual(new_invoice.state, 'posted')
        invoice_lines = new_invoice.invoice_line_ids
        other_lines = new_invoice.line_ids - invoice_lines
        self.assertEqual(invoice_lines.analytic_account_id, self.analytic_account)
        self.assertFalse(other_lines.analytic_account_id)
        self.assertEqual(invoice_lines.analytic_line_ids.account_id, self.analytic_account)
        ctx = {'active_model': 'account.move', 'active_ids': [new_invoice.id]}
        change = self.env['account.invoice.change'].with_context(ctx).create({})
        change.analytic_account_id = self.analytic_account2
        change.affect_change()
        self.assertEqual(invoice_lines.analytic_account_id, self.analytic_account2)
        self.assertFalse(other_lines.analytic_account_id)
        self.assertEqual(invoice_lines.analytic_line_ids.account_id, self.analytic_account2)
