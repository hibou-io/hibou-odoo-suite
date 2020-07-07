from odoo import fields, models


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    payslip_id = fields.Many2one('hr.payslip', string="Payslip", readonly=True)
