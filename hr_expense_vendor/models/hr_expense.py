from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HRExpense(models.Model):
    _inherit = 'hr.expense'

    vendor_id = fields.Many2one('res.partner', string='Vendor')

    def _prepare_move_line(self, line):
        values = super(HRExpense, self)._prepare_move_line(line)
        if self.payment_mode == 'company_account':
            if not self.vendor_id:
                raise ValidationError('You must have an assigned vendor to process a Company Paid Expense')
            values['partner_id'] = self.vendor_id.id
        name = values['name'] + (' - ' + str(self.reference) if self.reference else '')
        values['name'] = name[:64]
        return values


class HRExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    expense_line_ids = fields.One2many(states={'done': [('readonly', True)], 'post': [('readonly', True)]})
