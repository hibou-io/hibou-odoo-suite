# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models
from .us_payroll_config import FUTA_TYPE_NORMAL, \
                               FUTA_TYPE_BASIC, \
                               FUTA_TYPE_EXEMPT


class USHRContract(models.Model):
    _inherit = 'hr.contract'

    FUTA_TYPE_NORMAL = FUTA_TYPE_NORMAL
    FUTA_TYPE_BASIC = FUTA_TYPE_BASIC
    FUTA_TYPE_EXEMPT = FUTA_TYPE_EXEMPT

    us_payroll_config_id = fields.Many2one('hr.contract.us_payroll_config', 'Payroll Forms')
    external_wages = fields.Float(string='External Existing Wages')

    # Simplified fields for easier rules, state code will exempt based on contract's futa_type
    futa_type = fields.Selection(related='us_payroll_config_id.fed_940_type')

    def us_payroll_config_value(self, name):
        return self.us_payroll_config_id[name]
