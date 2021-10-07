# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    paid_hourly_timesheet = fields.Boolean(string="Paid Hourly Timesheet", default=False)

    @api.onchange('paid_hourly_timesheet')
    def _onchange_paid_hourly_timesheet(self):
        for contract in self:
            if contract.paid_hourly_timesheet:
                # only allow switch, not automatic switch 'back'
                contract.wage_type = 'hourly'
