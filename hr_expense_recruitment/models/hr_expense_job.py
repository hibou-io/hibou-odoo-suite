from odoo import api, fields, models


class HRExpenseJob(models.Model):
    _inherit = 'hr.expense'

    job_id = fields.Many2one('hr.job', string='Job')
