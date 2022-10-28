from odoo import api, fields, models


class HRJob(models.Model):
    _inherit = 'hr.job'

    company_currency = fields.Many2one('res.currency', string='Currency',
                                       related='company_id.currency_id', readonly=True)
    expense_total_amount = fields.Float(string='Expenses Total',
                                        compute='_compute_expense_total_amount',
                                        compute_sudo=True)
    expense_ids = fields.One2many('hr.expense', 'job_id', string='Expenses')

    @api.depends('expense_ids.total_amount')
    def _compute_expense_total_amount(self):
        for job in self:
            job.expense_total_amount = sum(job.expense_ids.mapped('total_amount'))
