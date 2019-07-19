from odoo import models, fields, api


class USIAHrContract(models.Model):
    _inherit = 'hr.contract'

    ia_w4_allowances = fields.Integer(string='Iowa W-4 allowances', default=0)
    ia_w4_additional_wh = fields.Float(string="Iowa Additional Withholding", default=0.0)
    ia_w4_tax_exempt = fields.Boolean(string="Tax Exempt")
