from odoo.addons.hr_expense.tests.test_expenses import TestCheckJournalEntry
from odoo.exceptions import ValidationError


class TestCheckVendor(TestCheckJournalEntry):

    def setUp(self):
        super(TestCheckVendor, self).setUp()
        self.vendor_id = self.env.ref('base.res_partner_3')

    def test_journal_entry_vendor(self):
        # Non company_account is handled by the super class's `test_journal_entry_
        self.expense.payment_mode = 'company_account'
        self.expense_line.payment_mode = 'company_account'

        # Submitted to Manager
        self.assertEquals(self.expense.state, 'submit', 'Expense is not in Reported state')
        # Approve
        self.expense.approve_expense_sheets()
        self.assertEquals(self.expense.state, 'approve', 'Expense is not in Approved state')
        # Create Expense Entries
        with self.assertRaises(ValidationError):
            self.expense.action_sheet_move_create()

        self.expense_line.vendor_id = self.vendor_id
        self.expense.action_sheet_move_create()
        self.assertEquals(self.expense.state, 'done')
        self.assertTrue(self.expense.account_move_id.id, 'Expense Journal Entry is not created')

        # [(line.debit, line.credit, line.tax_line_id.id) for line in self.expense.expense_line_ids.account_move_id.line_ids]
        # should git this result [(0.0, 700.0, False), (63.64, 0.0, 179), (636.36, 0.0, False)]
        for line in self.expense.account_move_id.line_ids:
            if line.credit:
                self.assertEqual(line.partner_id, self.vendor_id)
                self.assertAlmostEquals(line.credit, 700.00)
            else:
                if not line.tax_line_id == self.tax:
                    self.assertAlmostEquals(line.debit, 636.36)
                else:
                    self.assertAlmostEquals(line.debit, 63.64)
