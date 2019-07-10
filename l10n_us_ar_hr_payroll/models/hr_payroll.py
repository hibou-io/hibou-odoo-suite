from odoo import models, fields, api


class USARHrContract(models.Model):
    _inherit = 'hr.contract'

    ar_w4_allowances = fields.Integer(string='Arkansas W-4 allowances', default=0)
    ar_w4_additional_wh = fields.Float(string="Arkansas Additional Withholding", default=0.0)
    ar_w4_tax_exempt = fields.Boolean(string="Tax Exempt")
    ar_w4_texarkana_exemption = fields.Boolean(string="Texarkana Exemption")
