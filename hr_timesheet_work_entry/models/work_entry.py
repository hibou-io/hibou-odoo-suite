from odoo import fields, models


class HrWorkEntryType(models.Model):
    _inherit = 'hr.work.entry.type'

    allow_timesheet = fields.Boolean(string='Allow on Timesheet')
