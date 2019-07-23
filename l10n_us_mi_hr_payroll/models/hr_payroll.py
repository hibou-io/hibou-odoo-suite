from odoo import models, fields, api


class USMIHrContract(models.Model):
    _inherit = 'hr.contract'

    mi_w4_exemptions = fields.Integer(string='Michigan W-4 Allowances', default=0)
    mi_w4_additional_wh = fields.Float(string="Additional Withholding", default=0.0)
    mi_w4_tax_exempt = fields.Boolean(string="Tax Exempt")

