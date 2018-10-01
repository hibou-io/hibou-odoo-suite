from odoo.tests import common


class TestJobExpense(common.TransactionCase):
    def test_fields(self):
        job = self.env['hr.job'].create({'name': 'Test Job'})
        expense = self.env['hr.expense'].create({
            'name': 'Test Expense',
            'product_id': self.env['product.product'].search([('can_be_expensed', '=', True)], limit=1).id,
            'unit_amount': 34.0,
        })
        self.assertFalse(job.expense_ids)
        self.assertEqual(job.expense_total_amount, 0.0)
        expense.job_id = job
        self.assertTrue(job.expense_ids)
        self.assertEqual(job.expense_total_amount, 34.0)
