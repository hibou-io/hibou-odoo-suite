from odoo.addons.hr_expense.tests.test_expenses import TestExpenses
from odoo.tests import common


class TestCheckVendor(TestExpenses):
    def test_fields(self):
        lead = self.env['crm.lead'].create({'name': 'Test Lead'})
        expense = self.env['hr.expense'].create({
            'name': 'Test Expense',
            'product_id': self.product_a.id,
            'employee_id': self.expense_employee.id,
            'unit_amount': 34.0,
        })
        self.assertFalse(lead.expense_ids)
        self.assertEqual(lead.expense_total_amount, 0.0)
        expense.lead_id = lead
        self.assertTrue(lead.expense_ids)
        self.assertEqual(lead.expense_total_amount, 34.0)
