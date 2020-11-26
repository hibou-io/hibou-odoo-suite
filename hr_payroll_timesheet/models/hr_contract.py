# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    paid_hourly_timesheet = fields.Boolean(string="Paid Hourly Timesheet", default=False)
