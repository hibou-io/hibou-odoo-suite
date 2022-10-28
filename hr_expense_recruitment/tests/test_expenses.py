from odoo.addons.hr_expense.tests.common import TestExpenseCommon
from odoo.tests import tagged, Form



@tagged('-at_install', 'post_install')
class TestJobExpense(TestExpenseCommon):
    def test_fields(self):
        
        employee = self.env['hr.employee'].create({
            'name': 'Leo Pinedo',
        })
        job = self.env['hr.job'].create({'name': 'Test Job'})
        expense = self.env['hr.expense'].create({
            'name': 'Test Expense',
            'employee_id': self.expense_employee.id,
            'product_id': self.product_a.id,
            'unit_amount': 34.0,
        })
        self.assertTrue(job)
        self.assertTrue(expense)
        self.assertFalse(job.expense_ids)
        self.assertEqual(job.expense_total_amount, 0.0)
        expense.job_id = job
        self.assertTrue(job.expense_ids)
        self.assertEqual(job.expense_total_amount, 34.0)
