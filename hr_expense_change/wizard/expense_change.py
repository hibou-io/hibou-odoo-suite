from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ExpenseChangeWizard(models.TransientModel):
    _name = 'hr.expense.change'
    _description = 'Expense Change'

    expense_id = fields.Many2one('hr.expense', string='Expense', readonly=True, required=True)
    expense_company_id = fields.Many2one('res.company', related='expense_id.company_id')
    date = fields.Date(string='Expense Date')

    @api.model
    def default_get(self, fields):
        rec = super(ExpenseChangeWizard, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')

        # Checks on context parameters
        if not active_model or not active_ids:
            raise UserError(
                _("Programmation error: wizard action executed without active_model or active_ids in context."))
        if active_model != 'hr.expense':
            raise UserError(_(
                "Programmation error: the expected model for this action is 'hr.expense'. The provided one is '%d'.") % active_model)

        # Checks on received expense records
        expense = self.env[active_model].browse(active_ids)
        if len(expense) != 1:
            raise UserError(_("Expense Change expects only one expense."))
        rec.update({
            'expense_id': expense.id,
            'date': expense.date,
        })
        return rec

    def _new_expense_vals(self):
        vals = {}
        if self.expense_id.date != self.date:
            vals['date'] = self.date
        return vals

    def affect_change(self):
        self.ensure_one()
        vals = self._new_expense_vals()
        old_date = self.expense_id.date
        if vals:
            self.expense_id.write(vals)
        if 'date' in vals and self.expense_id.sheet_id.account_move_id:
            self.expense_id.sheet_id.account_move_id.write({'date': vals['date']})
            self.expense_id.sheet_id.account_move_id.line_ids\
                .filtered(lambda l: l.date_maturity == old_date).write({'date_maturity': vals['date']})
        return True
