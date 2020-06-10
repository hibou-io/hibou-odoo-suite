# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields, models


class HRContract(models.Model):
    _inherit = 'hr.contract'

    ira_amount = fields.Float(string="401K Contribution Amount",
                              help="Pre-Tax (traditional) Contribution Amount")
    ira_rate = fields.Float(string="401K Contribution (%)",
                            help="Pre-Tax (traditional) Contribution Percentage")
    ira_roth_amount = fields.Float(string="Roth 401K Contribution Amount",
                                   help="Post-Tax Contribution Amount")
    ira_roth_rate = fields.Float(string="Roth 401K Contribution (%)",
                                 help="Post-Tax Contribution Percentage")

    def company_401k_match_percent(self, payslip):
        # payslip is payslip rule's current payslip browse object
        # Override if you have employee, payslip, or contract differences.
        return payslip.rule_parameter('er_401k_match_percent')
