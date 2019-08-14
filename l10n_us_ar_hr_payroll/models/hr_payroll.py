from odoo import models, fields, api


class USARHrContract(models.Model):
    _inherit = 'hr.contract'

    ar_ar4ec_allowances = fields.Integer(string='Arkansas AR-4EC Allowances', default=0)
    ar_ar4ec_additional_wh = fields.Float(string="Arkansas AR-4EC Additional Withholding", default=0.0)
    ar_ar4ec_tax_exempt = fields.Boolean(string="Arkansas AR-4EC Tax Exempt")
    ar_ar4ec_texarkana_exemption = fields.Boolean(string="Arkansas AR-4EC Texarkana Exemption")
