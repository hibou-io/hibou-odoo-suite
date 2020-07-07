from odoo import fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    paid_hourly_timesheet = fields.Boolean(string="Paid Hourly Timesheet", default=False)
