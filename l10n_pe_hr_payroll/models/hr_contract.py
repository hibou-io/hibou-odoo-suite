# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class PEHRContract(models.Model):
    _inherit = 'hr.contract'
    
    pe_payroll_config_id = fields.Many2one('hr.contract.pe_payroll_config', 'Payroll Forms')
    pe_payroll_ee_4ta_cat_exempt = fields.Boolean(string='Exempt from 4th Cat. withholding.')
    
    def pe_payroll_config_value(self, name):
        return self.pe_payroll_config_id[name]
