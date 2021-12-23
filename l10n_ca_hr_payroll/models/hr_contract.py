# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class HRContract(models.Model):
    _inherit = 'hr.contract'

    ca_payroll_config_id = fields.Many2one('hr.contract.ca_payroll_config', 'Canada Payroll Forms')

    def ca_payroll_config_value(self, name):
        return self.ca_payroll_config_id[name]
