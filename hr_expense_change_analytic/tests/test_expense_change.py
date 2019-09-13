from odoo.addons.hr_expense_change.tests.test_expense_change import TestAccountEntry


class TestWizard(TestAccountEntry):
    def test_expense_change_basic(self):
        self.analytic_account = self.env['account.analytic.account'].create({
            'name': 'test account',
        })
        self.analytic_account2 = self.env['account.analytic.account'].create({
            'name': 'test account2',
        })

        self.expense.expense_line_ids.write({'analytic_account_id': False})

        super(TestWizard, self).test_expense_change_basic()

        # Tests Adding an Analytic Account
        self.assertFalse(self.expense.expense_line_ids.analytic_account_id)
        ctx = {'active_model': 'hr.expense', 'active_ids': self.expense.expense_line_ids.ids}
        change = self.env['hr.expense.change'].with_context(ctx).create({})
        change.analytic_account_id = self.analytic_account
        change.affect_change()
        self.assertEqual(self.expense.expense_line_ids.analytic_account_id, self.analytic_account)

        # Tests Changing
        change.analytic_account_id = self.analytic_account2
        change.affect_change()
        self.assertEqual(self.expense.expense_line_ids.analytic_account_id, self.analytic_account2)

        # Tests Removing
        change.analytic_account_id = False
        change.affect_change()
        self.assertFalse(self.expense.expense_line_ids.analytic_account_id)
