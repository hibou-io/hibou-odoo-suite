from odoo.addons.hr_expense.tests.common import TestExpenseCommon
from odoo.exceptions import UserError
from odoo.tests import Form, tagged


@tagged('-at_install', 'post_install')
class TestCheckVendor(TestExpenseCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super(TestCheckVendor, cls).setUpClass(chart_template_ref=chart_template_ref)
        cls.vendor_id = cls.env.ref('base.res_partner_3')
        cls.tax = cls.env['account.tax'].create({
            'name': 'Expense 10%',
            'amount': 10,
            'amount_type': 'percent',
            'type_tax_use': 'purchase',
            'price_include': True,
        })

    def test_journal_entry_vendor(self):
        expense_form = Form(self.env['hr.expense'])
        expense_form.name = 'Car Travel Expenses'
        expense_form.employee_id = self.expense_employee
        expense_form.product_id = self.product_zero_cost
        expense_form.total_amount = 700.00
        expense_form.tax_ids.clear()
        expense_form.tax_ids.add(self.tax)
        expense_form.payment_mode = 'company_account'
        expense = expense_form.save()

        action_submit_expenses = expense.action_submit_expenses()
        expense_sheet_form = Form(self.env[action_submit_expenses['res_model']].with_context(**action_submit_expenses.get('context', {})))
        expense_sheet = expense_sheet_form.save()
        
        self.assertEqual(expense_sheet.state, 'draft', 'Expense is not in Draft state')
        expense_sheet.action_submit_sheet()

        self.assertEqual(expense_sheet.state, 'submit', 'Expense is not in Submitted state')
        # Approve
        expense_sheet.approve_expense_sheets()
        self.assertEqual(expense_sheet.state, 'approve', 'Expense is not in Approved state')
        # Create Expense Entries
        with self.assertRaises(UserError):
            expense_sheet.action_sheet_move_create()

        expense.vendor_id = self.vendor_id
        expense_sheet.action_sheet_move_create()
        self.assertEqual(expense_sheet.state, 'done')
        self.assertTrue(expense_sheet.account_move_id.id, 'Expense Journal Entry is not created')

        # [(line.debit, line.credit, line.tax_line_id.id) for line in expense_sheet.account_move_id.line_ids]
        # should get this result [(0.0, 700.0, False), (63.64, 0.0, 179), (636.36, 0.0, False)]
        for line in expense_sheet.account_move_id.line_ids:
            if line.credit:
                self.assertEqual(line.partner_id, self.vendor_id)
                self.assertAlmostEqual(line.credit, 700.00)
            else:
                if not line.tax_line_id == self.tax:
                    self.assertAlmostEqual(line.debit, 636.36)
                else:
                    self.assertAlmostEqual(line.debit, 63.64)
