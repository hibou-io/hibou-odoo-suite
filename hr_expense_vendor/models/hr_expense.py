from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HRExpense(models.Model):
    _inherit = 'hr.expense'

    vendor_id = fields.Many2one('res.partner', string='Vendor')

    def _get_account_move_line_values(self):
        move_line_values_by_expense = super(HRExpense, self)._get_account_move_line_values()
        for expense in self.filtered(lambda e: e.payment_mode == 'company_account'):
            if not expense.vendor_id:
                raise ValidationError('You must have an assigned vendor to process a Company Paid Expense')
            move_line_values = move_line_values_by_expense[expense.id]
            for line_values in move_line_values:
                new_name = expense.name.split('\n')[0][:64] + (' - ' + str(expense.reference) if expense.reference else '')
                line_values['name'] = new_name[:64]
                line_values['partner_id'] = expense.vendor_id.id
        return move_line_values_by_expense


class HRExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    expense_line_ids = fields.One2many(states={'done': [('readonly', True)], 'post': [('readonly', True)]})
