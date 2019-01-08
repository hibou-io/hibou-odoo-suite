from odoo import models, fields, api


class USOHHrContract(models.Model):
    _inherit = 'hr.contract'

    oh_income_allowances = fields.Integer(string='Ohio Income Allowances', default=0)
    oh_additional_withholding = fields.Float(string="Additional Withholding", default=0.0)
