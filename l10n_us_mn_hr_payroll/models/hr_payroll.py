from odoo import models, fields, api


class USMNHrContract(models.Model):
    _inherit = 'hr.contract'

    mn_w4mn_allowances = fields.Integer(string="MN Allowances")
    mn_w4mn_additional_wh = fields.Float(string="MN Additional Withholding")
    mn_w4mn_filing_status = fields.Selection([
        ('exempt', 'Exempt'),
        ('single', 'Single'),
        ('married', 'Married'),
    ], string='MN Filing Status')
