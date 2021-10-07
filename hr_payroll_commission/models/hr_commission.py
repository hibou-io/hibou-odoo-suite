# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields, models, _


class CommissionPayment(models.Model):
    _inherit = 'hr.commission.payment'

    pay_in_payslip = fields.Boolean(string="Reimburse In Next Payslip")
    payslip_id = fields.Many2one('hr.payslip', string="Payslip", readonly=True)

    def action_report_in_next_payslip(self):
        self.filtered(lambda p: not p.payslip_id).write({'pay_in_payslip': True})
