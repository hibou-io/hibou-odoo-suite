from odoo.addons.hr_expense_change.tests import test_expense_change
from odoo.tests import tagged
from odoo import fields


@tagged('-at_install', 'post_install')
class TestWizard(test_expense_change.TestAccountEntry):

    def test_expense_change_basic(self):
        super(TestWizard, self).test_expense_values()

        # Tests Adding an Analytic Account

        self.analytic_account = self.env['account.analytic.account'].create({
            'name': 'test account',
        })
        self.analytic_account2 = self.env['account.analytic.account'].create({
            'name': 'test account2',
        })

        self.assertNotEqual(self.expense.analytic_account_id, self.analytic_account)
        ctx = {'active_model': 'hr.expense', 'active_ids': self.expense.ids}
        change = self.env['hr.expense.change'].sudo().with_context(ctx).create({})
        change.analytic_account_id = self.analytic_account
        change.affect_change()
        self.assertEqual(self.expense.analytic_account_id, self.analytic_account)

        # Tests Changing
        change.analytic_account_id = self.analytic_account2
        change.affect_change()
        self.assertEqual(self.expense.analytic_account_id, self.analytic_account2)

        # Tests Removing
        change.analytic_account_id = False
        change.affect_change()
        self.assertFalse(self.expense.analytic_account_id)
