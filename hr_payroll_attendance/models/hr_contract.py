# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import models, fields


class HrContract(models.Model):
    _inherit = 'hr.contract'

    paid_hourly_attendance = fields.Boolean(string="Paid Hourly Attendance")
