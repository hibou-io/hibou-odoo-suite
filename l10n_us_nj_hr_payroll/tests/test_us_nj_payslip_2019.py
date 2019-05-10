from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip


class TestUsNJPayslip(TestUsPayslip):
    ###
    #   2018 Taxes and Rates
    ###
    NJ_UNEMP_MAX_WAGE = 34400.0  # Note that this is used for SDI and FLI as well

    ER_NJ_UNEMP = -2.6825 / 100.0
    EE_NJ_UNEMP = -0.3825 / 100.0

    ER_NJ_SDI = -0.5 / 100.0
    EE_NJ_SDI = -0.17 / 100.0

    ER_NJ_WF = -0.1175 / 100.0
    EE_NJ_WF = -0.0425 / 100.0

    ER_NJ_FLI = 0.0
    EE_NJ_FLI = -0.08 / 100.0

    # Examples found on page 24 of http://www.state.nj.us/treasury/taxation/pdf/current/njwt.pdf
    def test_2019_taxes_example1(self):
        salary = 300
        schedule_pay = 'weekly'
        allowances = 1
        additional_withholding = 0

        # Tax Percentage Method for Single, taxable under $385
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

        self._log('2019 New Jersey tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_NJ_UNEMP'], salary)
        self.assertPayrollEqual(cats['EE_US_NJ_UNEMP'], round(cats['BASIC'] * self.EE_NJ_UNEMP, 2))
        self.assertPayrollEqual(cats['ER_US_NJ_UNEMP'], round(cats['WAGE_US_NJ_UNEMP'] * self.ER_NJ_UNEMP, 2))
        self.assertPayrollEqual(cats['EE_US_NJ_SDI'], cats['WAGE_US_NJ_SDI'] * self.EE_NJ_SDI)
        self.assertPayrollEqual(cats['ER_US_NJ_SDI'], cats['WAGE_US_NJ_SDI'] * self.ER_NJ_SDI)
        self.assertPayrollEqual(cats['EE_US_NJ_FLI'], cats['WAGE_US_NJ_FLI'] * self.EE_NJ_FLI)
        self.assertPayrollEqual(cats['EE_US_NJ_WF'], cats['WAGE_US_NJ_WF'] * self.EE_NJ_WF)
        self.assertPayrollEqual(cats['EE_US_NJ_INC_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_nj_unemp_wages = self.NJ_UNEMP_MAX_WAGE - salary if (self.NJ_UNEMP_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2019 New Jersey tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_NJ_UNEMP'], remaining_nj_unemp_wages)
        self.assertPayrollEqual(cats['ER_US_NJ_UNEMP'], round(remaining_nj_unemp_wages * self.ER_NJ_UNEMP, 2))
        self.assertPayrollEqual(cats['EE_US_NJ_UNEMP'], round(cats['BASIC'] * self.EE_NJ_UNEMP, 2))

    def test_2019_taxes_example2(self):
        salary = 1400.00
        schedule_pay = 'weekly'
        allowances = 3
        additional_withholding = 0

        # Tax Percentage Method for Single, taxable pay over $769, under $1442
        wh = -27.58

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

        self._log('2019 New Jersey tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_NJ_UNEMP'], salary)
        self.assertPayrollEqual(cats['EE_US_NJ_UNEMP'], cats['WAGE_US_NJ_UNEMP'] * self.EE_NJ_UNEMP)
        #self.assertPayrollEqual(cats['ER_US_NJ_UNEMP'], round(cats['WAGE_US_NJ_UNEMP'] * self.ER_NJ_UNEMP, 2))
        # round(37.555, 2) => 37.55 but in reality this should be 37.56, floats are weird ;)
        self.assertTrue(abs(cats['ER_US_NJ_UNEMP'] - round(cats['WAGE_US_NJ_UNEMP'] * self.ER_NJ_UNEMP, 2)) < 0.02)
        self.assertPayrollEqual(cats['EE_US_NJ_SDI'], cats['WAGE_US_NJ_SDI'] * self.EE_NJ_SDI)
        self.assertPayrollEqual(cats['ER_US_NJ_SDI'], cats['WAGE_US_NJ_SDI'] * self.ER_NJ_SDI)
        self.assertPayrollEqual(cats['EE_US_NJ_FLI'], cats['WAGE_US_NJ_FLI'] * self.EE_NJ_FLI)
        self.assertPayrollEqual(cats['EE_US_NJ_WF'], cats['WAGE_US_NJ_WF'] * self.EE_NJ_WF)
        self.assertPayrollEqual(cats['EE_US_NJ_INC_WITHHOLD'], wh)

        process_payslip(payslip)

    def test_2019_taxes_to_the_limits(self):
        salary = 30000.00
        schedule_pay = 'quarterly'
        allowances = 3
        additional_withholding = 0

        # Tax Percentage Method for Single, taxable pay over $18750, under 125000
        wh = -1021.75

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref(
                                            'l10n_us_nj_hr_payroll.hr_payroll_salary_structure_us_nj_employee'),
                                        schedule_pay=schedule_pay)
        contract.nj_njw4_allowances = allowances
        contract.nj_additional_withholding = additional_withholding
        contract.nj_njw4_filing_status = 'married_joint'

        self.assertEqual(contract.schedule_pay, 'quarterly')

        self._log('2019 New Jersey tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-03-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_NJ_UNEMP'], salary)
        self.assertPayrollEqual(cats['EE_US_NJ_UNEMP'], cats['BASIC'] * self.EE_NJ_UNEMP)
        #self.assertPayrollEqual(cats['ER_US_NJ_UNEMP'], round(cats['WAGE_US_NJ_UNEMP'] * self.ER_NJ_UNEMP, 2))
        # round(37.555, 2) => 37.55 but in reality this should be 37.56, floats are weird ;)
        self.assertTrue(abs(cats['ER_US_NJ_UNEMP'] - round(cats['WAGE_US_NJ_UNEMP'] * self.ER_NJ_UNEMP, 2)) < 0.02)
        self.assertPayrollEqual(cats['EE_US_NJ_SDI'], cats['WAGE_US_NJ_SDI'] * self.EE_NJ_SDI)
        self.assertPayrollEqual(cats['ER_US_NJ_SDI'], cats['WAGE_US_NJ_SDI'] * self.ER_NJ_SDI)
        self.assertPayrollEqual(cats['EE_US_NJ_FLI'], cats['WAGE_US_NJ_FLI'] * self.EE_NJ_FLI)
        self.assertPayrollEqual(cats['ER_US_NJ_WF'], cats['WAGE_US_NJ_WF'] * self.ER_NJ_WF)
        self.assertPayrollEqual(cats['EE_US_NJ_WF'], cats['WAGE_US_NJ_WF'] * self.EE_NJ_WF)
        self.assertPayrollEqual(cats['EE_US_NJ_INC_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_nj_unemp_wages = self.NJ_UNEMP_MAX_WAGE - salary if (self.NJ_UNEMP_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2019 New Jersey tax second payslip:')
        payslip = self._createPayslip(employee, '2019-04-01', '2019-07-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertFalse(abs(cats['BASIC'] - remaining_nj_unemp_wages) < 0.02)
        self.assertTrue(abs(cats['WAGE_US_NJ_UNEMP'] - remaining_nj_unemp_wages) < 0.02)
        self.assertPayrollEqual(cats['WAGE_US_NJ_UNEMP'], remaining_nj_unemp_wages)
        self.assertPayrollEqual(cats['ER_US_NJ_UNEMP'], round(remaining_nj_unemp_wages * self.ER_NJ_UNEMP, 2))
        self.assertPayrollEqual(cats['EE_US_NJ_UNEMP'], round(remaining_nj_unemp_wages * self.EE_NJ_UNEMP, 2))
        self.assertPayrollEqual(cats['EE_US_NJ_SDI'], remaining_nj_unemp_wages * self.EE_NJ_SDI)
        self.assertPayrollEqual(cats['ER_US_NJ_SDI'], remaining_nj_unemp_wages * self.ER_NJ_SDI)
        self.assertPayrollEqual(cats['EE_US_NJ_WF'], remaining_nj_unemp_wages * self.EE_NJ_WF)
        self.assertPayrollEqual(cats['ER_US_NJ_WF'], remaining_nj_unemp_wages * self.ER_NJ_WF)
