from odoo.addons.hr_expense.tests.test_expenses import TestAccountEntry
from odoo.exceptions import ValidationError


class TestCheckVendor(TestAccountEntry):

    def setUp(self):
        super(TestCheckVendor, self).setUp()
        self.vendor_id = self.env.ref('base.res_partner_3')

    def test_journal_entry_vendor(self):
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
        expense.payment_mode = 'company_account'
        expense_line.payment_mode = 'company_account'
        expense_line._onchange_product_id()

        # State should default to draft
        self.assertEquals(expense.state, 'draft', 'Expense should be created in Draft state')
        # Submitted to Manager
        expense.action_submit_sheet()
        self.assertEquals(expense.state, 'submit', 'Expense is not in Reported state')
        # Approve
        expense.approve_expense_sheets()
        self.assertEquals(expense.state, 'approve', 'Expense is not in Approved state')
        # Create Expense Entries
        with self.assertRaises(ValidationError):
            expense.action_sheet_move_create()

        expense_line.vendor_id = self.vendor_id
        expense.action_sheet_move_create()
        self.assertEquals(expense.state, 'done')
        self.assertTrue(expense.account_move_id.id, 'Expense Journal Entry is not created')

        # [(line.debit, line.credit, line.tax_line_id.id) for line in self.expense.expense_line_ids.account_move_id.line_ids]
        # should git this result [(0.0, 700.0, False), (63.64, 0.0, 179), (636.36, 0.0, False)]
        for line in expense.account_move_id.line_ids:
            if line.credit:
                self.assertEqual(line.partner_id, self.vendor_id)
                self.assertAlmostEquals(line.credit, 700.00)
            else:
                if not line.tax_line_id == self.tax:
                    self.assertAlmostEquals(line.debit, 636.36)
                else:
                    self.assertAlmostEquals(line.debit, 63.64)
