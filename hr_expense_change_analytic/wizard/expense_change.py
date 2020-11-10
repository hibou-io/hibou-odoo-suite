from odoo import api, fields, models, _


class ExpenseChangeWizard(models.TransientModel):
    _inherit = 'hr.expense.change'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_account_warning = fields.Char(string='Analytic Account Warning', compute='_compute_analytic_warning')

    @api.model
    def default_get(self, fields):
        rec = super(ExpenseChangeWizard, self).default_get(fields)
        expense = self.env['hr.expense'].browse(rec['expense_id'])
        rec.update({
            'analytic_account_id': expense.analytic_account_id.id,
        })
        return rec

    @api.onchange('expense_id', 'analytic_account_id')
    def _compute_analytic_warning(self):
        self.ensure_one()
        expenses = self._find_expenses_to_write_analytic(self.expense_id.analytic_account_id.id)
        if len(expenses) <= 1:
            self.analytic_account_warning = ''
        else:
            other_expenses = expenses - self.expense_id
            self.analytic_account_warning = '%d other expenses will be changed. (%s)' % \
                                            (len(other_expenses), ', '.join(other_expenses.mapped('name')))



    def affect_change(self):
        old_analytic_id = self.expense_id.analytic_account_id.id
        res = super(ExpenseChangeWizard, self).affect_change()
        self._affect_analytic_change(old_analytic_id)
        return res

    def _find_expenses_to_write_analytic(self, old_analytic_id):
        if self.analytic_account_id.id == old_analytic_id:
            return []
        # Essentially, if you have a move, you must write all related expenses and lines.
        if not self.expense_id.sheet_id.account_move_id:
            return self.expense_id
        return self.expense_id.sheet_id.expense_line_ids\
                   .filtered(lambda l: l.analytic_account_id.id == old_analytic_id)

    def _affect_analytic_change(self, old_analytic_id):
        expenses_to_affect = self._find_expenses_to_write_analytic(old_analytic_id)
        if expenses_to_affect:
            expenses_to_affect.write({'analytic_account_id': self.analytic_account_id.id})

            lines_to_affect = self.expense_id.sheet_id.account_move_id \
                .line_ids.filtered(lambda l: l.analytic_account_id.id == old_analytic_id and l.debit)
            lines_to_affect.write({'analytic_account_id': self.analytic_account_id.id})
            lines_to_affect.create_analytic_lines()
