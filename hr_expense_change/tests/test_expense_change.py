from odoo import fields
from odoo.addons.hr_expense.tests.common import TestExpenseCommon


class TestExpenseChange(TestExpenseCommon):

    def setUp(self):
        super(TestExpenseChange, self).setUp()

        self.setUpAdditionalAccounts()

        self.product_expense = self.env['product.product'].create({
            'name': "Delivered at cost",
            'standard_price': 700,
            'list_price': 700,
            'type': 'consu',
            'supplier_taxes_id': [(6, 0, [self.tax.id])],
            'default_code': 'CONSU-DELI-COST',
            'taxes_id': False,
            'property_account_expense_id': self.account_expense.id,
        })

    def test_expense_change_basic(self):
        # post expense and get move ready at expense.account_move_id.id
        expense = self.env['hr.expense.sheet'].create({
            'name': 'Expense for John Smith',
            'employee_id': self.employee.id,
        })
        expense_line = self.env['hr.expense'].create({
            'name': 'Car Travel Expenses',
            'employee_id': self.employee.id,
            'product_id': self.product_expense.id,
            'unit_amount': 700.00,
            'tax_ids': [(6, 0, [self.tax.id])],
            'sheet_id': expense.id,
            'analytic_account_id': self.analytic_account.id,
        })
        expense_line._onchange_product_id()
        # Submitted to Manager
        expense.action_submit_sheet()
        # Approve
        expense.approve_expense_sheets()
        # Create Expense Entries
        expense.action_sheet_move_create()
        self.assertEquals(expense.state, 'post', 'Expense is not in Waiting Payment state')

        ctx = {'active_model': 'hr.expense', 'active_ids': expense.expense_line_ids.ids}
        change = self.env['hr.expense.change'].with_context(ctx).create({})
        self.assertEqual(change.date, expense.expense_line_ids.date)

        change_date = '2018-01-01'
        change.write({'date': change_date})

        change.affect_change()
        self.assertEqual(change_date, fields.Date.to_string(expense.expense_line_ids.date))
        self.assertEqual(change_date, fields.Date.to_string(expense.account_move_id.date))
