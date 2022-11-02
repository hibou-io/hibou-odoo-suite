from odoo import api, fields, models


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    expense_total_amount = fields.Float(string='Expenses Total',
                                        compute='_compute_expense_total_amount',
                                        compute_sudo=True)
    expense_ids = fields.One2many('hr.expense', 'lead_id', string='Expenses')

    @api.depends('expense_ids.total_amount')
    def _compute_expense_total_amount(self):
        for lead in self:
            lead.expense_total_amount = sum(lead.expense_ids.mapped('total_amount'))
