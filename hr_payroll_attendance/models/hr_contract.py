# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, models, fields


class HrContract(models.Model):
    _inherit = 'hr.contract'

    paid_hourly_attendance = fields.Boolean(string="Paid Hourly Attendance")

    @api.onchange('paid_hourly_attendance')
    def _onchange_paid_hourly_attendance(self):
        for contract in self:
            if contract.paid_hourly_attendance:
                # only allow switch, not automatic switch 'back'
                contract.wage_type = 'hourly'
