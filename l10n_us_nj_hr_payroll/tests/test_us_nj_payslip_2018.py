from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip


class TestUsNJPayslip(TestUsPayslip):
    ###
    #   2018 Taxes and Rates
    ###
    NJ_UNEMP_MAX_WAGE = 33700.0
    EE_NJ_UNEMP = -0.3825 / 100.0
    ER_NJ_UNEMP = -3.4 / 100.0
    EE_NJ_SDI = -0.24 / 100.0
    ER_NJ_SDI = -0.5 / 100.0
    EE_NJ_FLI = -0.1 / 100.0
    ER_NJ_FLI = 0.0
    EE_NJ_WF = -0.0425 / 100.0
    ER_NJ_WF = 0.0

    # Examples found on page 24 of http://www.state.nj.us/treasury/taxation/pdf/current/njwt.pdf
    def test_2018_taxes_example1(self):
        salary = 300
        schedule_pay = 'weekly'
        allowances = 1
        additional_withholding = 0

        # Tax Percentage Method for Single, taxable pay over $58, under $346
        wh = -4.21

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref(
                                            'l10n_us_nj_hr_payroll.hr_payroll_salary_structure_us_nj_employee'),
                                        schedule_pay=schedule_pay)
        contract.nj_njw4_allowances = allowances
        contract.nj_additional_withholding = additional_withholding
        contract.nj_njw4_filing_status = 'single'
        contract.nj_njw4_rate_table = 'A'

        self.assertEqual(contract.schedule_pay, 'weekly')

        self._log('2018 New Jersey tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_NJ_UNEMP'], salary)
        self.assertPayrollEqual(cats['EE_US_NJ_UNEMP'], round(cats['BASIC'] * self.EE_NJ_UNEMP, 2))
        self.assertPayrollEqual(cats['ER_US_NJ_UNEMP'], cats['WAGE_US_NJ_UNEMP'] * self.ER_NJ_UNEMP)
        self.assertPayrollEqual(cats['EE_US_NJ_SDI'], cats['BASIC'] * self.EE_NJ_SDI)
        self.assertPayrollEqual(cats['ER_US_NJ_SDI'], cats['WAGE_US_NJ_SDI'] * self.ER_NJ_SDI)
        self.assertPayrollEqual(cats['EE_US_NJ_FLI'], cats['BASIC'] * self.EE_NJ_FLI)
        self.assertPayrollEqual(cats['EE_US_NJ_WF'], cats['BASIC'] * self.EE_NJ_WF)
        self.assertPayrollEqual(cats['EE_US_NJ_INC_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_nj_unemp_wages = self.NJ_UNEMP_MAX_WAGE - salary if (self.NJ_UNEMP_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2018 New Jersey tax second payslip:')
        payslip = self._createPayslip(employee, '2018-02-01', '2018-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_NJ_UNEMP'], remaining_nj_unemp_wages)
        self.assertPayrollEqual(cats['ER_US_NJ_UNEMP'], remaining_nj_unemp_wages * self.ER_NJ_UNEMP)
        self.assertPayrollEqual(cats['EE_US_NJ_UNEMP'], cats['BASIC'] * self.EE_NJ_UNEMP)

    def test_2018_taxes_example2(self):
        salary = 1400.00
        schedule_pay = 'weekly'
        allowances = 3
        additional_withholding = 0

        # Tax Percentage Method for Single, taxable pay over $58, under $346
        wh = -27.60

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref(
                                            'l10n_us_nj_hr_payroll.hr_payroll_salary_structure_us_nj_employee'),
                                        schedule_pay=schedule_pay)
        contract.nj_njw4_allowances = allowances
        contract.nj_additional_withholding = additional_withholding
        contract.nj_njw4_filing_status = 'married_joint'

        self.assertEqual(contract.schedule_pay, 'weekly')

        self._log('2018 New Jersey tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_NJ_UNEMP'], salary)
        self.assertPayrollEqual(cats['EE_US_NJ_UNEMP'], cats['BASIC'] * self.EE_NJ_UNEMP)
        self.assertPayrollEqual(cats['ER_US_NJ_UNEMP'], cats['WAGE_US_NJ_UNEMP'] * self.ER_NJ_UNEMP)
        self.assertPayrollEqual(cats['EE_US_NJ_SDI'], cats['BASIC'] * self.EE_NJ_SDI)
        self.assertPayrollEqual(cats['ER_US_NJ_SDI'], cats['WAGE_US_NJ_SDI'] * self.ER_NJ_SDI)
        self.assertPayrollEqual(cats['EE_US_NJ_FLI'], cats['BASIC'] * self.EE_NJ_FLI)
        self.assertPayrollEqual(cats['EE_US_NJ_WF'], cats['BASIC'] * self.EE_NJ_WF)
        self.assertPayrollEqual(cats['EE_US_NJ_INC_WITHHOLD'], wh)

        process_payslip(payslip)
