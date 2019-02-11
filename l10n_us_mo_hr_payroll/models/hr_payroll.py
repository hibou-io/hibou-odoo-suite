from odoo import models, fields, api


class USMOHrContract(models.Model):
    _inherit = 'hr.contract'

    mo_mow4_filing_status = fields.Selection([
        ('', 'Exempt'),
        ('single', 'Single'),
        ('married', 'Married'),
        ('head_of_household', 'Head of Household'),
    ], string='Federal W4 Filing Status', default='single')
    mo_mow4_spouse_employed = fields.Boolean(string='Missouri W-4 Spouse Employed', default=False)
    mo_mow4_exemptions = fields.Integer(string='Missouri W-4 Exemptions', default=0,
                                        help="As of 2019, there are no longer allowances"
                                             " in the Missouri Withholding tables.")
    mo_mow4_additional_withholding = fields.Float(string="Missouri W-4 Additional Withholding", default=0.0)
