from odoo import models, fields


class USMSHrContract(models.Model):
    _inherit = 'hr.contract'

    ms_89_350_filing_status = fields.Selection([
        ('', 'Exempt (e.g. Box 8)'),
        ('single', 'Single'),
        ('married', 'Married (spouse NOT employed)'),
        ('married_dual', 'Married (spouse IS employed)'),
        ('head_of_household', 'Head of Household'),
    ], string='Mississippi 89-350 Filing Status', default='single')

    ms_89_350_exemption = fields.Float(string='Mississippi 89-350 Exemptions', default=0.0,
                                       help='Box 6')
    ms_89_350_additional_withholding = fields.Float(string="Mississippi 89-350 Additional Withholding", default=0.0,
                                                 help='Box 7')
