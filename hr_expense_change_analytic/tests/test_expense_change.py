from odoo.addons.hr_expense.tests.common import TestExpenseCommon


class TestWizard(TestExpenseCommon):
    def setUp(self):
        super(TestWizard, self).setUp()

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

    def test_expense_change_analytic(self):
        analytic_account = self.env['account.analytic.account'].create({
            'name': 'test account',
        })
        analytic_account2 = self.env['account.analytic.account'].create({
            'name': 'test account2',
        })

        # post expense and get move ready at expense.account_move_id.id
        expense = self.env['hr.expense.sheet'].create({
            'name': 'Expense for John Smith',
            'employee_id': self.employee.id,
            'expense_line_ids': [
                (0, 0, {
                    'name': 'Coffee Expenses',
                    'employee_id': self.employee.id,
                    'product_id': self.product_expense.id,
                    'unit_amount': 10.00,
                    'tax_ids': [(6, 0, [self.tax.id])],
                    'analytic_account_id': False,
                }),
                (0, 0, {
                    'name': 'Car Travel Expenses',
                    'employee_id': self.employee.id,
                    'product_id': self.product_expense.id,
                    'unit_amount': 700.00,
                    'tax_ids': [(6, 0, [self.tax.id])],
                    'analytic_account_id': False,
                }),
            ],
        })
        # expense_line = self.env['hr.expense'].create()
        for expense_line in expense.expense_line_ids:
            expense_line._onchange_product_id()
        # Submitted to Manager
        expense.action_submit_sheet()
        # Approve
        expense.approve_expense_sheets()
        # Create Expense Entries
        expense.action_sheet_move_create()
        self.assertEquals(expense.state, 'post', 'Expense is not in Waiting Payment state')

        # Tests Adding an Analytic Account
        self.assertFalse(any(expense.expense_line_ids.mapped('analytic_account_id')))
        ctx = {'active_model': 'hr.expense', 'active_ids': [expense.expense_line_ids[0].id]}
        change = self.env['hr.expense.change'].with_context(ctx).create({})
        change.analytic_account_id = analytic_account
        change.affect_change()
        self.assertEqual(expense.expense_line_ids.mapped('analytic_account_id'), analytic_account)

        # Tests Changing
        change.analytic_account_id = analytic_account2
        change.affect_change()
        self.assertEqual(expense.expense_line_ids.mapped('analytic_account_id'), analytic_account2)

        # Tests Removing
        change.analytic_account_id = False
        change.affect_change()
        self.assertFalse(any(expense.expense_line_ids.mapped('analytic_account_id')))
