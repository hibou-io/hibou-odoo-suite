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

    def nj_unemp_employee_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'nj_unemp_employee_rate_' + str(year)):
            return self.employee_id.company_id['nj_unemp_employee_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US New Jersey.')

    def nj_unemp_company_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'nj_unemp_company_rate_' + str(year)):
            return self.employee_id.company_id['nj_unemp_company_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US New Jersey.')

    def nj_sdi_company_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'nj_sdi_company_rate_' + str(year)):
            return self.employee_id.company_id['nj_sdi_company_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US New Jersey.')

    def nj_sdi_employee_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'nj_sdi_employee_rate_' + str(year)):
            return self.employee_id.company_id['nj_sdi_employee_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US New Jersey.')

    def nj_fli_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'nj_fli_rate_' + str(year)):
            return self.employee_id.company_id['nj_fli_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US New Jersey.')

    def nj_wf_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'nj_wf_rate_' + str(year)):
            return self.employee_id.company_id['nj_wf_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US New Jersey.')


class NJCompany(models.Model):
    _inherit = 'res.company'

    nj_unemp_company_rate_2018 = fields.Float(string="New Jersey Employer State Unemployment Insurance Rate 2018", default=3.4)
    nj_unemp_employee_rate_2018 = fields.Float(string="New Jersey Employee State Unemployment Insurance Rate 2018", default=0.3825)
    nj_sdi_company_rate_2018 = fields.Float(string="New Jersey Employer State Disability Insurance Rate 2018", default=0.5)
    nj_sdi_employee_rate_2018 = fields.Float(string="New Jersey Employee State Disability Insurance Rate 2018", default=0.19)
    nj_fli_rate_2018 = fields.Float(string="New Jersey Family Leave Insurance Rate 2018", default=0.09)
    nj_wf_rate_2018 = fields.Float(string="New Jersey Workforce Development Rate 2018", default=0.0)
