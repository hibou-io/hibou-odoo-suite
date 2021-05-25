from odoo import api, fields, models


class CAHRContract(models.Model):
    _inherit = 'hr.contract'

    ca_payroll_config_id = fields.Many2one('hr.contract.ca_payroll_config', 'Canada Payroll Forms')



