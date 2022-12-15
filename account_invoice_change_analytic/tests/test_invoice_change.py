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
        self.assertFalse(self.invoice_basic.invoice_line_ids.mapped('analytic_account_id'))
        ctx = {'active_model': 'account.move', 'active_ids': [self.invoice_basic.id]}
        change = self.env['account.invoice.change'].with_context(ctx).create({})
        change.analytic_account_id = self.analytic_account
        change.affect_change()
        self.assertTrue(self.invoice_basic.invoice_line_ids.mapped('analytic_account_id'))

        # Tests Removing Analytic Account
        new_invoice = self.invoice_basic.copy()
        new_invoice.invoice_line_ids.analytic_account_id = self.analytic_account
        new_invoice.action_invoice_open()
        self.assertEqual(new_invoice.state, 'open')
        ctx = {'active_model': 'account.move', 'active_ids': [new_invoice.id]}
        change = self.env['account.invoice.change'].with_context(ctx).create({})
        change.analytic_account_id = False
        change.affect_change()
        self.assertFalse(new_invoice.invoice_line_ids.mapped('analytic_account_id'))

        # Tests Changing Analytic Account
        new_invoice = self.invoice_basic.copy()
        new_invoice.invoice_line_ids.analytic_account_id = self.analytic_account
        new_invoice.action_invoice_open()
        self.assertEqual(new_invoice.state, 'open')
        ctx = {'active_model': 'account.move', 'active_ids': [new_invoice.id]}
        change = self.env['account.invoice.change'].with_context(ctx).create({})
        change.analytic_account_id = self.analytic_account2
        change.affect_change()
