from odoo import models, fields, api


class USNJHrContract(models.Model):
    _inherit = 'hr.contract'

    nj_njw4_allowances = fields.Integer(string="New Jersey NJ-W4 Allowances",
                                      default=0,
                                      help="Allowances claimed on NJ W-4")
    nj_additional_withholding = fields.Float(string="Additional Withholding",
                                              default=0.0,
                                              help='Additional withholding from line 5 of form NJ-W4')
    nj_njw4_filing_status = fields.Selection([
        ('single', 'Single'),
        ('married_separate', 'Married/Civil Union partner Separate'),
        ('married_joint', 'Married/Civil Union Couple Joint'),
        ('widower', 'Widower/Surviving Civil Union Partner'),
        ('head_household', 'Head of Household')
    ], string='NJ Filing Status', default='single')
    nj_njw4_rate_table = fields.Char(string='Wage Chart Letter',
                                    help='Wage Chart Letter from line 3 of form NJ-W4.')
