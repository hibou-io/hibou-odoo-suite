from odoo import api, fields, models


class SalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    account_debit = fields.Many2one('account.account', company_dependent=True)
    account_credit = fields.Many2one('account.account', company_dependent=True)
    analytic_account_id = fields.Many2one('account.analytic.account', company_dependent=True)
    account_tax_id = fields.Many2one('account.tax', company_dependent=True)
