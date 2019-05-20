from odoo.tests import common


class TestCheckVendor(common.TransactionCase):
    def test_fields(self):
        lead = self.env['crm.lead'].create({'name': 'Test Lead'})
        expense = self.env['hr.expense'].create({
            'name': 'Test Expense',
            'product_id': self.env['product.product'].search([('can_be_expensed', '=', True)], limit=1).id,
            'employee_id': self.env['hr.employee'].search([], limit=1).id,
            'unit_amount': 34.0,
        })
        self.assertFalse(lead.expense_ids)
        self.assertEqual(lead.expense_total_amount, 0.0)
        expense.lead_id = lead
        self.assertTrue(lead.expense_ids)
        self.assertEqual(lead.expense_total_amount, 34.0)
