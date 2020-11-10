from odoo.addons.hr_expense.tests import test_expenses
from odoo.tests import tagged
from odoo import fields


@tagged('-at_install', 'post_install')
class TestAccountEntry(test_expenses.TestExpenses):

    def test_expense_values(self):
        """ Checking accounting move entries and analytic entries when submitting expense """

        # The expense employee is able to a create an expense sheet.
        # The total should be 1725.0 because:
        # - first line: 1000.0 (unit amount) + 150.0 (tax) = 1150.0
        # - second line: (1500.0 (unit amount) + 225.0 (tax)) * 1/3 (rate) = 575.0.

        expense_sheet = self.env['hr.expense.sheet'].create({
            'name': 'First Expense for employee',
            'employee_id': self.expense_employee.id,
            'journal_id': self.company_data['default_journal_purchase'].id,
            'accounting_date': '2017-01-01',
            'expense_line_ids': [
                (0, 0, {
                    # Expense without foreign currency.
                    'name': 'expense_1',
                    'date': '2016-01-01',
                    'product_id': self.product_a.id,
                    'unit_amount': 1000.0,
                    'tax_ids': [(6, 0, self.company_data['default_tax_purchase'].ids)],
                    'analytic_account_id': self.analytic_account_1.id,
                    'employee_id': self.expense_employee.id,
                }),
                (0, 0, {
                    # Expense with foreign currency (rate 1:3).
                    'name': 'expense_1',
                    'date': '2016-01-01',
                    'product_id': self.product_b.id,
                    'unit_amount': 1500.0,
                    'tax_ids': [(6, 0, self.company_data['default_tax_purchase'].ids)],
                    'analytic_account_id': self.analytic_account_2.id,
                    'currency_id': self.currency_data['currency'].id,
                    'employee_id': self.expense_employee.id,
                }),
            ],
        })

        # Check expense sheet values.
        self.assertRecordValues(expense_sheet, [{'state': 'draft', 'total_amount': 1725.0}])

        expense_sheet.action_submit_sheet()
        expense_sheet.approve_expense_sheets()
        expense_sheet.action_sheet_move_create()

        # Check expense sheet journal entry values.
        self.assertRecordValues(expense_sheet.account_move_id.line_ids.sorted('balance'), [
            # Receivable line (company currency):
            {
                'debit': 0.0,
                'credit': 1150.0,
                'amount_currency': -1150.0,
                'account_id': self.company_data['default_account_payable'].id,
                'product_id': False,
                'currency_id': self.company_data['currency'].id,
                'tax_line_id': False,
                'analytic_account_id': False,
            },
            # Receivable line (foreign currency):
            {
                'debit': 0.0,
                'credit': 862.5,
                'amount_currency': -1725.0,
                'account_id': self.company_data['default_account_payable'].id,
                'product_id': False,
                'currency_id': self.currency_data['currency'].id,
                'tax_line_id': False,
                'analytic_account_id': False,
            },
            # Tax line (foreign currency):
            {
                'debit': 112.5,
                'credit': 0.0,
                'amount_currency': 225.0,
                'account_id': self.company_data['default_account_tax_purchase'].id,
                'product_id': False,
                'currency_id': self.currency_data['currency'].id,
                'tax_line_id': self.company_data['default_tax_purchase'].id,
                'analytic_account_id': False,
            },
            # Tax line (company currency):
            {
                'debit': 150.0,
                'credit': 0.0,
                'amount_currency': 150.0,
                'account_id': self.company_data['default_account_tax_purchase'].id,
                'product_id': False,
                'currency_id': self.company_data['currency'].id,
                'tax_line_id': self.company_data['default_tax_purchase'].id,
                'analytic_account_id': False,
            },
            # Product line (foreign currency):
            {
                'debit': 750.0,
                'credit': 0.0,
                'amount_currency': 1500.0,
                'account_id': self.company_data['default_account_expense'].id,
                'product_id': self.product_b.id,
                'currency_id': self.currency_data['currency'].id,
                'tax_line_id': False,
                'analytic_account_id': self.analytic_account_2.id,
            },
            # Product line (company currency):
            {
                'debit': 1000.0,
                'credit': 0.0,
                'amount_currency': 1000.0,
                'account_id': self.company_data['default_account_expense'].id,
                'product_id': self.product_a.id,
                'currency_id': self.company_data['currency'].id,
                'tax_line_id': False,
                'analytic_account_id': self.analytic_account_1.id,
            },
        ])

        # Check expense analytic lines.
        self.assertRecordValues(expense_sheet.account_move_id.line_ids.analytic_line_ids.sorted('amount'), [
            {
                'amount': -1000.0,
                'date': fields.Date.from_string('2017-01-01'),
                'account_id': self.analytic_account_1.id,
                'currency_id': self.company_data['currency'].id,
            },
            {
                'amount': -750.0,
                'date': fields.Date.from_string('2017-01-01'),
                'account_id': self.analytic_account_2.id,
                'currency_id': self.company_data['currency'].id,
            },
        ])
        
        # actual test
        self.assertEqual(expense_sheet.accounting_date, expense_sheet.account_move_id.date)

        expense = expense_sheet.expense_line_ids[0]

        ctx = {'active_model': 'hr.expense', 'active_ids': expense.ids}
        change = self.env['hr.expense.change'].sudo(flag=True).with_context(ctx).create({})
        self.assertEqual(change.date, expense.date)

        change_date = '2018-01-01'
        change.write({'date': change_date})

        change.affect_change()
        self.assertEqual(change_date, str(expense.date))
        self.assertEqual(change_date, str(expense_sheet.account_move_id.date))
