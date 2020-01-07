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
                                       help='Code for a Rule Parameter, used by some states or your own rules.')
    workers_comp_er_code = fields.Char(string='Workers\' Comp Code (Employer Withholding)',
                                       help='Code for a Rule Parameter, used by some states or your own rules.')

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

    al_a4_sit_exemptions = fields.Selection([
        ('', '0'),
        ('S', 'S'),
        ('MS', 'MS'),
        ('M', 'M'),
        ('H', 'H'),
    ], string='Alabama A4 Withholding Exemptions', help='A4 1. 2. 3.')
    al_a4_sit_dependents = fields.Integer(string='Alabama A4 Dependents', help='A4 4.')

    ar_ar4ec_sit_allowances = fields.Integer(string='Arkansas AR4EC allowances', help='AR4EC 3.')

    az_a4_sit_withholding_percentage = fields.Float(
        string='Arizona A-4 Withholding Percentage',
        help='A-4 1. (0.8 or 1.3 or 1.8 or 2.7 or 3.6 or 4.2 or 5.1 or 0 for exempt.')

    ca_de4_sit_allowances = fields.Integer(string='California W-4 Allowances',
                                           help='CA W-4 3.')
    ca_de4_sit_additional_allowances = fields.Integer(string='California W-4 Additional Allowances',
                                                      help='CA W-4 4(c).')
    ca_de4_sit_filing_status = fields.Selection([
        ('', 'Exempt'),
        ('single', 'Single or Married filing separately'),
        ('married', 'Married filing jointly'),
        ('head_household', 'Head of Household')
    ], string='California W-4 Filing Status', help='CA W-4 1(c).')

    ct_w4na_sit_code = fields.Selection([
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
        ('d', 'D'),
        ('f', 'F'),
    ], string='Connecticut CT-W4 Withholding Code', help='CT-W4 1.')

    de_w4_sit_filing_status = fields.Selection([
        ('single', 'Single or Married filing separately'),
        ('married', 'Married filing jointly'),
    ], string='Delaware W-4 Marital Status', help='DE W-4 3.')
    de_w4_sit_dependent = fields.Integer(string='Delaware W-4 Dependents', help='DE W-4 4.')

    ga_g4_sit_filing_status = fields.Selection([
        ('', 'Exempt'),
        ('single', 'Single'),
        ('married filing joint, both spouses working', 'Married Filing Joint, both spouses working'),
        ('married filing joint, one spouse working', 'Married Filing Joint, one spouse working'),
        ('married filing separate', 'Married Filing Separate'),
        ('head of household', 'Head of Household'),
    ], string='Georgia G-4 Filing Status', help='G-4 3.')
    ga_g4_sit_dependent_allowances = fields.Integer(string='Georgia G-4 Dependent Allowances',
                                                    help='G-4 4.')
    ga_g4_sit_additional_allowances = fields.Integer(string='Georgia G-4 Additional Allowances',
                                                     help='G-4 5.')

    hi_hw4_sit_filing_status = fields.Selection([
        ('', 'Exempt'),
        ('single', 'Single'),
        ('married', 'Married'),
        ('head_of_household', 'Head of Household'),
    ], string='Hawaii HW-4 Marital Status', help='HI HW-4 3.')
    hi_hw4_sit_allowances = fields.Integer(string='Hawaii HW-4 Allowances', help='HI HW-4 4.')

    ia_w4_sit_allowances = fields.Integer(string='Iowa W-4 allowances', help='IA W-4 6.')

    id_w4_sit_filing_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('head of household', 'Head of Household'),
    ], string='Idaho ID W-4 Withholding Status', help='ID W-4 A.B.C.')
    id_w4_sit_allowances = fields.Integer(string='Idaho ID W-4 Allowances', help='ID W-4 1.')

    il_w4_sit_basic_allowances = fields.Integer(string='Illinois IL-W-4 Number of Basic Allowances', help='IL-W-4 Step 1.')
    il_w4_sit_additional_allowances = fields.Integer(string='Illinois IL-W-4 Number of Additional Allowances', help='IL-W-4 Step 2.')

    in_w4_sit_personal_exemption = fields.Integer(string='Indiana In-W-4 Number of Personal Exemption', help='IN-W-4 5.')
    in_w4_sit_dependent_exemption = fields.Integer(string='Indiana In-W-4 Number of Dependent Exemption', help='IN-W-4 6.')

    ks_k4_sit_filing_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Joint'),
    ], string='Kansas K-4 Filing Status', help='KS K-4 3.')
    ks_k4_sit_allowances = fields.Integer(string='Kansas KS K-4 Number of Allowances', help='KS K-4 Step 4.')

    la_l4_sit_filing_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
    ], string='Louisiana LA L-4 Filing Status', help='LA L-4 3.')
    la_l4_sit_exemptions = fields.Integer(string='Louisiana LA L-4 Number of Exemptions', help='LA L-4 6.')
    la_l4_sit_dependents = fields.Integer(string='Louisiana LA L-4 Number of Dependents', help='LA L-4 7.')

    me_w4me_sit_filing_status = fields.Selection([
        ('', 'Exempt'),
        ('single', 'Single or Head of Household'),
        ('married', 'Married'),
    ], string='Maine W-4ME Filing Status', help='ME W-4ME 3.')
    me_w4me_sit_allowances = fields.Integer(string='Maine Allowances', help='W-4ME 4.')

    mi_w4_sit_exemptions = fields.Integer(string='Michigan MI W-4 Exemptions', help='MI-W4 6.')

    mn_w4mn_sit_filing_status = fields.Selection([
        ('', 'Exempt'),
        ('single', 'Single'),
        ('married', 'Married'),
    ], string='Minnesota W-4MN Marital Status', help='W-4MN')
    mn_w4mn_sit_allowances = fields.Integer(string='Minnesota Allowances', help='W-4MN 1.')

    mo_mow4_sit_filing_status = fields.Selection([
        ('', 'Exempt'),
        ('single', 'Single or Married Spouse Works or Married Filing Separate'),
        ('married', 'Married (Spouse does not work)'),
        ('head_of_household', 'Head of Household'),
    ], string='Missouri W-4 Filing Status', help='MO W-4 1.')
    mo_mow4_sit_withholding = fields.Integer(string='Missouri MO W-4 Reduced Withholding', help='MO W-4 3.')

    ms_89_350_sit_filing_status = fields.Selection([
        ('', 'Exempt'),
        ('single', 'Single'),
        ('married', 'Married (spouse NOT employed)'),
        ('married_dual', 'Married (spouse IS employed)'),
        ('head_of_household', 'Head of Household'),
    ], string='Mississippi 89-350 Filing Status', help='89-350 1. 2. 3. 8.')
    ms_89_350_sit_exemption_value = fields.Float(string='Mississippi 89-350 Exemption Total',
                                                 help='89-350 Box 6 (including filing status amounts)')

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

    nc_nc4_sit_filing_status = fields.Selection([
        ('', 'Exempt'),
        ('single', 'Single'),
        ('married', 'Married'),
        ('head_household', 'Head of Household')
    ], string='North Carolina NC-4 Filing Status', help='NC-4')
    nc_nc4_sit_allowances = fields.Integer(string='North Carolina NC-4 Allowances', help='NC-4 1.')

    nd_w4_sit_filing_status = fields.Selection([
        ('', 'Exempt'),
        ('single', 'Single'),
        ('married', 'Married'),
        ('head_household', 'Head of Household')
    ], string='North Dakota ND W-4 Filing Status', help='ND W-4')
    nd_w4_sit_allowances = fields.Integer(string='North Dakota ND W-4')

    ne_w4n_sit_filing_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
    ], string='Nebraska NE W-4N Filing Status', help='NE W-4N')
    ne_w4n_sit_allowances = fields.Integer(string='Nebraska NE W-4N Allowances', help='NE W-4N 1.')

    nj_njw4_sit_filing_status = fields.Selection([
        ('', 'Exempt'),
        ('single', 'Single'),
        ('married_separate', 'Married/Civil Union partner Separate'),
        ('married_joint', 'Married/Civil Union Couple Joint'),
        ('widower', 'Widower/Surviving Civil Union Partner'),
        ('head_household', 'Head of Household')
    ], string='New Jersey NJ-W4 Filing Status', help='NJ-W4 2.')
    nj_njw4_sit_allowances = fields.Integer(string='New Jersey NJ-W4 Allowances', help='NJ-W4 4.')
    nj_njw4_sit_rate_table = fields.Selection([
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('E', 'E')
    ], string='New Jersey Wage Chart Letter', help='NJ-W4. 3.')

    ny_it2104_sit_filing_status = fields.Selection([
        ('', 'Exempt'),
        ('single', 'Single'),
        ('married', 'Married'),
    ], string='New York NY IT-2104 Filing Status', help='NY IT-2104')
    ny_it2104_sit_allowances = fields.Integer(string="New York IT-2104 Allowances", help="NY IT-2104 1. 2.")

    # Ohio will use generic SIT exempt and additional fields
    oh_it4_sit_exemptions = fields.Integer(string='Ohio IT-4 Exemptions',
                                           help='Line 4')

    ok_w4_sit_filing_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('head_household', 'Married, but withhold at higher Single rate')
    ], string='Oklahoma OK-W-4 Filing Status', help='OK-W-4')
    ok_w4_sit_allowances = fields.Integer(string='Oklahoma OK-W-4 Allowances', help='OK-W-4 5.')

    ri_w4_sit_allowances = fields.Integer(string='Rhode Island RI W-4 Allowances', help='RI W-4 1.')

    sc_w4_sit_allowances = fields.Integer(string='South Carolina SC W-4 Allowances', help='SC W-4 5.')

    ut_w4_sit_filing_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('head_household', 'Head of Household')
    ], string='Utah UT W-4 Filing Status', help='UT W-4 C.')

    vt_w4vt_sit_filing_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
    ], string='Vermont VT W-4VT Filing Status', help='VT W-4VT')
    vt_w4vt_sit_allowances = fields.Integer(string='Vermont VT W-4VT Allowances', help='VT W-4VT 5.')

    va_va4_sit_exemptions = fields.Integer(string='Virginia VA-4(P) Personal Exemptions',
                                           help='VA-4(P) 1(a)')
    va_va4_sit_other_exemptions = fields.Integer(string='Virginia VA-4(P) Age & Blindness Exemptions',
                                                 help='VA-4(P) 1(b)')

    wi_wt4_sit_filing_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
    ], string='Wisconsin WT-4 Filing Status', help='WI WT-4')
    wi_wt4_sit_exemptions = fields.Integer(string='Wisconsin Exemptions', help='WI WT-4 1.(d)')

    wv_it104_sit_filing_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('head_household', 'Head of Household')
    ], string='West Virginia WV/IT-104 Filing Status', help='WV WV/IT-104')
    wv_it104_sit_exemptions = fields.Integer(string='West Virginia Exemptions', help='WV WV/IT-104 4.')
