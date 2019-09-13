from odoo.addons.hr_expense.tests.test_expenses import TestAccountEntry


class TestAccountEntry(TestAccountEntry):

    def test_expense_change_basic(self):
        # posts expense and gets move ready at self.expense.account_move_id.id
        self.test_account_entry()
        self.assertEqual(self.expense.expense_line_ids.date, self.expense.account_move_id.date)

        ctx = {'active_model': 'hr.expense', 'active_ids': self.expense.expense_line_ids.ids}
        change = self.env['hr.expense.change'].with_context(ctx).create({})
        self.assertEqual(change.date, self.expense.expense_line_ids.date)

        change_date = '2018-01-01'
        change.write({'date': change_date})

        change.affect_change()
        self.assertEqual(change_date, self.expense.expense_line_ids.date)
        self.assertEqual(change_date, self.expense.account_move_id.date)
