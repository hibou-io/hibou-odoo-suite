# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models

FUTA_TYPE_EXEMPT = 'exempt'
FUTA_TYPE_BASIC = 'basic'
FUTA_TYPE_NORMAL = 'normal'


class HRContractUSPayrollConfig(models.Model):
    _name = 'hr.contract.us_payroll_config'
    _description = 'Contract US Payroll Forms'

    name = fields.Char(string="Description")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    state_id = fields.Many2one('res.country.state', string="Applied State")
    state_code = fields.Char(related='state_id.code')
    state_income_tax_exempt = fields.Boolean(string='State Income Tax Exempt')
    state_income_tax_additional_withholding = fields.Float(string='State Income Tax Additional Withholding')
    workers_comp_ee_code = fields.Char(string='Workers\' Comp Code (Employee Withholding)',
                                       help='Code for a Payroll Rate, used by some states or your own rules.')
    workers_comp_er_code = fields.Char(string='Workers\' Comp Code (Employer Withholding)',
                                       help='Code for a Payroll Rate, used by some states or your own rules.')

    fed_940_type = fields.Selection([
        (FUTA_TYPE_EXEMPT, 'Exempt (0%)'),
        (FUTA_TYPE_NORMAL, 'Normal Net Rate (0.6%)'),
        (FUTA_TYPE_BASIC, 'Basic Rate (6%)'),
    ], string="Federal Unemployment Tax Type (FUTA)", default='normal')

    fed_941_fica_exempt = fields.Boolean(string='FICA Exempt', help="Exempt from Social Security and "
                                                                    "Medicare e.g. F1 Student Visa")

    fed_941_fit_w4_filing_status = fields.Selection([
        ('', 'Exempt'),
        ('single', 'Single or Married filing separately'),
        ('married', 'Married filing jointly'),
        ('married_as_single', 'Head of Household'),
    ], string='Federal W4 Filing Status [1(c)]', default='single')
    fed_941_fit_w4_allowances = fields.Integer(string='Federal W4 Allowances (before 2020)')
    fed_941_fit_w4_is_nonresident_alien = fields.Boolean(string='Federal W4 Is Nonresident Alien')
    fed_941_fit_w4_multiple_jobs_higher = fields.Boolean(string='Federal W4 Multiple Jobs Higher [2(c)]',
                                                         help='Form W4 (2020+) 2(c) Checkbox. '
                                                              'Uses Higher Withholding tables.')
    fed_941_fit_w4_dependent_credit = fields.Float(string='Federal W4 Dependent Credit [3]',
                                                   help='Form W4 (2020+) Line 3')
    fed_941_fit_w4_other_income = fields.Float(string='Federal W4 Other Income [4(a)]',
                                               help='Form W4 (2020+) 4(a)')
    fed_941_fit_w4_deductions = fields.Float(string='Federal W4 Deductions [4(b)]',
                                             help='Form W4 (2020+) 4(b)')
    fed_941_fit_w4_additional_withholding = fields.Float(string='Federal W4 Additional Withholding [4(c)]',
                                                         help='Form W4 (2020+) 4(c)')

    mt_mw4_sit_exemptions = fields.Integer(string='Montana MW-4 Exemptions',
                                           help='MW-4 Box G')
    # Don't use the main state_income_tax_exempt because of special meaning and reporting
    # Use additional withholding but name it on the form 'MW-4 Box H'
    mt_mw4_sit_exempt = fields.Selection([
        ('', 'Not Exempt'),
        ('tribe', 'Registered Tribe'),
        ('reserve', 'Reserve or National Guard'),
        ('north_dakota', 'North Dakota'),
        ('montana_for_marriage', 'Montana for Marriage'),
    ], string='Montana MW-4 Exempt from Withholding', help='MW-4 Section 2')

    # Ohio will use generic SIT exempt and additional fields
    oh_it4_sit_exemptions = fields.Integer(string='Ohio IT-4 Exemptions',
                                           help='Line 4')

    va_va4_sit_exemptions = fields.Integer(string='Virginia VA-4(P) Personal Exemptions',
                                           help='VA-4(P) 1(a)')
    va_va4_sit_other_exemptions = fields.Integer(string='Virginia VA-4(P) Age & Blindness Exemptions',
                                           help='VA-4(P) 1(b)')
