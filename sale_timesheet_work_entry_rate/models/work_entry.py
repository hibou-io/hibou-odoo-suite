# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields, models


class HrWorkEntryType(models.Model):
    _inherit = 'hr.work.entry.type'

    timesheet_billing_rate = fields.Float(string='Timesheet Billing Multiplier', default=1.0)
