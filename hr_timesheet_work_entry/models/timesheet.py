from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    work_type_id = fields.Many2one('hr.work.entry.type', string='Work Type',
                                   default=lambda self: self.env.ref('hr_timesheet_work_entry.work_input_timesheet',
                                                                     raise_if_not_found=False))
