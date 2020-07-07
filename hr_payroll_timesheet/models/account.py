from odoo import fields, models


class AnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    payslip_id = fields.Many2one('hr.payslip', string="Payslip", readonly=True)
