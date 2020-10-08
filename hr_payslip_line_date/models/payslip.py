from odoo import models, fields


class PayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    date = fields.Date(string="Date Account", related='slip_id.date', store=True)