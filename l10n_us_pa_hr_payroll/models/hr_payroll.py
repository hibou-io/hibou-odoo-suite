from odoo import models, fields, api


class USPAHrContract(models.Model):
    _inherit = 'hr.contract'

    pa_additional_withholding = fields.Float(string="Additional Withholding")
