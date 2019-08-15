from odoo import models, fields, api


class USARHrContract(models.Model):
    _inherit = 'hr.contract'

    ar_ar4ec_allowances = fields.Integer(string='Arkansas AR-4EC Allowances',
                                         oldname='ar_w4_allowances')
    ar_ar4ec_additional_wh = fields.Float(string="Arkansas AR-4EC Additional Withholding",
                                          oldname='ar_w4_additional_wh')
    ar_ar4ec_tax_exempt = fields.Boolean(string='Arkansas AR-4EC Tax Exempt',
                                         oldname='ar_w4_tax_exempt')
    ar_ar4ec_texarkana_exemption = fields.Boolean(string='Arkansas AR-4EC Texarkana Exemption',
                                                  oldname='ar_w4_texarkana_exemption')
