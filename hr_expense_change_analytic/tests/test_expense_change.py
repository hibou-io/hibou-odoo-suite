from odoo.addons.hr_expense.tests.common import TestExpenseCommon
from odoo.tests import tagged
from odoo import fields


@tagged('-at_install', 'post_install')
class TestWizard(TestExpenseCommon):

    def test_expense_change_analytic(self):
        expense_sheet = self.env['hr.expense.sheet'].create({
            'name': 'First Expense for employee',
            'employee_id': self.expense_employee.id,
            'journal_id': self.company_data['default_journal_purchase'].id,
            'accounting_date': '2017-01-01',
            'expense_line_ids': [
                (0, 0, {
                    'name': 'expense_1',
                    'date': '2016-01-01',
                    'product_id': self.product_a.id,
                    'unit_amount': 1000.0,
                    'tax_ids': [(6, 0, self.company_data['default_tax_purchase'].ids)],
                    'analytic_account_id': False,
                    'employee_id': self.expense_employee.id,
                }),
                (0, 0, {
                    'name': 'expense_2',
                    'date': '2016-01-01',
                    'product_id': self.product_a.id,
                    'unit_amount': 500.0,
                    'tax_ids': [(6, 0, self.company_data['default_tax_purchase'].ids)],
                    'analytic_account_id': False,
                    'employee_id': self.expense_employee.id,
                }),
            ],
        })

        expense_sheet.action_submit_sheet()
        expense_sheet.approve_expense_sheets()
        expense_sheet.action_sheet_move_create()

        # Tests Adding an Analytic Account
        self.assertFalse(any(expense_sheet.expense_line_ids.mapped('analytic_account_id')))
        ctx = {'active_model': 'hr.expense', 'active_ids': [expense_sheet.expense_line_ids[0].id]}
        change = self.env['hr.expense.change'].sudo().with_context(ctx).create({})
        change.analytic_account_id = self.analytic_account_1
        change.affect_change()
        self.assertEqual(expense_sheet.expense_line_ids.mapped('analytic_account_id'), self.analytic_account_1)

        # Tests Changing
        change.analytic_account_id = self.analytic_account_2
        change.affect_change()
        self.assertEqual(expense_sheet.expense_line_ids.mapped('analytic_account_id'), self.analytic_account_2)

        # Tests Removing
        change.analytic_account_id = False
        change.affect_change()
        self.assertFalse(any(expense_sheet.expense_line_ids.mapped('analytic_account_id')))
