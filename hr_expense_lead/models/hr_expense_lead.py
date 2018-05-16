from odoo import api, fields, models


class HRExpenseLead(models.Model):
    _inherit = 'hr.expense'

    lead_id = fields.Many2one('crm.lead', string='Lead')
