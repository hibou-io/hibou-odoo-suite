from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip
from odoo.addons.l10n_us_hr_payroll.l10n_us_hr_payroll import USHrContract


class TestUsNJPayslip(TestUsPayslip):
    ###
    #   2018 Taxes and Rates
    ###
    NJ_UNEMP_MAX_WAGE = 33700.0

    # Examples found on page 24 of http://www.state.nj.us/treasury/taxation/pdf/current/njwt.pdf
    def test_2018_taxes_example1(self):
        salary = 300
        schedule_pay = 'weekly'
        allowances = 1
        additional_withholding = 0

        # Tax Percentage Method for Single, taxable pay over $58, under $346
        wh = -4.21

        employee = self._createEmployee()
        employee.company_id.nj_unemp_employee = 0.3825
        employee.company_id.nj_unemp_company = 3.4
        employee.company_id.nj_sdi_employee = 0.19
        employee.company_id.nj_sdi_company = 0.5
        employee.company_id.nj_fli = 0.09
        employee.company_id.nj_wf = 0.0

        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref(
                                            'l10n_us_nj_hr_payroll.hr_payroll_salary_structure_us_nj_employee'),
                                        schedule_pay=schedule_pay)
        contract.nj_njw4_allowances = allowances
        contract.nj_additional_withholding = additional_withholding
        contract.nj_njw4_filing_status = 'single'
        contract.nj_njw4_rate_table = 'A'

        # tax rates
        nj_unemp_employee = contract.nj_unemp_employee_rate(2018) / -100.0
        nj_unemp_company = contract.nj_unemp_company_rate(2018) / -100.0
        nj_sdi_employee = contract.nj_sdi_employee_rate(2018) / -100.0
        nj_sdi_company = contract.nj_sdi_company_rate(2018) / -100.0
        nj_fli = contract.nj_fli_rate(2018) / -100.0
        nj_wf = contract.nj_wf_rate(2018) / -100.0

        self.assertEqual(contract.schedule_pay, 'weekly')

        self._log('2018 New Jersey tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NJ_UNEMP_WAGES'], salary)
        self.assertPayrollEqual(cats['NJ_UNEMP_EMPLOYEE'], round(cats['NJ_UNEMP_WAGES'] * nj_unemp_employee, 2))
        self.assertPayrollEqual(cats['NJ_UNEMP_COMPANY'], cats['NJ_UNEMP_WAGES'] * nj_unemp_company)
        self.assertPayrollEqual(cats['NJ_SDI_EMPLOYEE'], cats['NJ_SDI_WAGES'] * nj_sdi_employee)
        self.assertPayrollEqual(cats['NJ_SDI_COMPANY'], cats['NJ_SDI_WAGES'] * nj_sdi_company)
        self.assertPayrollEqual(cats['NJ_FLI'], cats['NJ_FLI_WAGES'] * nj_fli)
        self.assertPayrollEqual(cats['NJ_WF'], cats['NJ_WF_WAGES'] * nj_wf)
        self.assertPayrollEqual(cats['NJ_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_nj_unemp_wages = self.NJ_UNEMP_MAX_WAGE - salary if (self.NJ_UNEMP_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2018 New Jersey tax second payslip:')
        payslip = self._createPayslip(employee, '2018-02-01', '2018-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NJ_UNEMP_WAGES'], remaining_nj_unemp_wages)
        self.assertPayrollEqual(cats['NJ_UNEMP_COMPANY'], remaining_nj_unemp_wages * nj_unemp_company)
        self.assertPayrollEqual(cats['NJ_UNEMP_EMPLOYEE'], remaining_nj_unemp_wages * nj_unemp_employee)

    def test_2018_taxes_example2(self):
        salary = 1400.00
        schedule_pay = 'weekly'
        allowances = 3
        additional_withholding = 0

        # Tax Percentage Method for Single, taxable pay over $58, under $346
        wh = -27.60

        employee = self._createEmployee()
        employee.company_id.nj_unemp_employee = 0.3825
        employee.company_id.nj_unemp_company = 3.4
        employee.company_id.nj_sdi_employee = 0.19
        employee.company_id.nj_sdi_company = 0.5
        employee.company_id.nj_fli = 0.09
        employee.company_id.nj_wf = 0.0

        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref(
                                            'l10n_us_nj_hr_payroll.hr_payroll_salary_structure_us_nj_employee'),
                                        schedule_pay=schedule_pay)
        contract.nj_njw4_allowances = allowances
        contract.nj_additional_withholding = additional_withholding
        contract.nj_njw4_filing_status = 'married_joint'

        # tax rates
        nj_unemp_employee = contract.nj_unemp_employee_rate(2018) / -100.0
        nj_unemp_company = contract.nj_unemp_company_rate(2018) / -100.0
        nj_sdi_employee = contract.nj_sdi_employee_rate(2018) / -100.0
        nj_sdi_company = contract.nj_sdi_company_rate(2018) / -100.0
        nj_fli = contract.nj_fli_rate(2018) / -100.0
        nj_wf = contract.nj_wf_rate(2018) / -100.0

        self.assertEqual(contract.schedule_pay, 'weekly')

        self._log('2018 New Jersey tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NJ_UNEMP_WAGES'], salary)
        self.assertPayrollEqual(cats['NJ_UNEMP_EMPLOYEE'], round((cats['NJ_UNEMP_WAGES'] * nj_unemp_employee), 2))
        self.assertPayrollEqual(cats['NJ_UNEMP_COMPANY'], cats['NJ_UNEMP_WAGES'] * nj_unemp_company)
        self.assertPayrollEqual(cats['NJ_SDI_EMPLOYEE'], cats['NJ_SDI_WAGES'] * nj_sdi_employee)
        self.assertPayrollEqual(cats['NJ_SDI_COMPANY'], cats['NJ_SDI_WAGES'] * nj_sdi_company)
        self.assertPayrollEqual(cats['NJ_FLI'], cats['NJ_FLI_WAGES'] * nj_fli)
        self.assertPayrollEqual(cats['NJ_WF'], cats['NJ_WF_WAGES'] * nj_wf)
        self.assertPayrollEqual(cats['NJ_WITHHOLD'], wh)

        process_payslip(payslip)
