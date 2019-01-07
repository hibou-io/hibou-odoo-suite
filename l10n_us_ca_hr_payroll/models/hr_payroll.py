from odoo import models, fields, api


class USCAHrContract(models.Model):
    _inherit = 'hr.contract'

    ca_de4_allowances = fields.Integer(string="California CA-4 Allowances",
                                       default=0,
                                       help="Estimated Deductions claimed on DE-4")
    ca_additional_allowances = fields.Integer(string="Additional Allowances", default=0)
    ca_de4_filing_status = fields.Selection([
        ('exempt', 'Exempt'),
        ('single', 'Single'),
        ('married', 'Married'),
        ('head_household', 'Head of Household')
    ], string='CA Filing Status', default='single')
