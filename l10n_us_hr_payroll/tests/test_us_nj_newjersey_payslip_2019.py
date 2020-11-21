# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip


class TestUsNJPayslip(TestUsPayslip):
    ###
    #   2019 Taxes and Rates
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

        # Tax Percentage Method for Single, taxable under $385
        wh = -4.21

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('NJ'),
                                        nj_njw4_sit_filing_status='single',
                                        nj_njw4_sit_allowances=1,
                                        state_income_tax_additional_withholding=0.0,
                                        nj_njw4_sit_rate_table='A',
                                        schedule_pay='weekly')

        self._log('2019 New Jersey tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_SUTA'], salary * (self.EE_NJ_UNEMP + self.EE_NJ_SDI + self.EE_NJ_WF + self.EE_NJ_FLI))
        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * (self.ER_NJ_UNEMP + self.ER_NJ_SDI + self.ER_NJ_WF + self.ER_NJ_FLI))
        self.assertTrue(all((cats['EE_US_SUTA'], cats['ER_US_SUTA'])))
        # self.assertPayrollEqual(cats['EE_US_NJ_SDI_SIT'], cats['EE_US_NJ_SDI_SIT'] * self.EE_NJ_SDI)
        # self.assertPayrollEqual(cats['ER_US_NJ_SDI_SUTA'], cats['ER_US_NJ_SDI_SUTA'] * self.ER_NJ_SDI)
        # self.assertPayrollEqual(cats['EE_US_NJ_FLI_SIT'], cats['EE_US_NJ_FLI_SIT'] * self.EE_NJ_FLI)
        # self.assertPayrollEqual(cats['EE_US_NJ_WF_SIT'], cats['EE_US_NJ_WF_SIT'] * self.EE_NJ_WF)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)

        # # Make a new payslip, this one will have maximums
        #
        remaining_nj_unemp_wages = self.NJ_UNEMP_MAX_WAGE - salary if (self.NJ_UNEMP_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2019 New Jersey tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        # self.assertPayrollEqual(cats['WAGE_US_NJ_UNEMP'], remaining_nj_unemp_wages)
        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_nj_unemp_wages * (self.ER_NJ_UNEMP + self.ER_NJ_SDI + self.ER_NJ_WF + self.ER_NJ_FLI))
        self.assertPayrollEqual(cats['EE_US_SUTA'], remaining_nj_unemp_wages * (self.EE_NJ_UNEMP + self.EE_NJ_SDI + self.EE_NJ_WF + self.EE_NJ_FLI))

    def test_2019_taxes_example2(self):
        salary = 1400.00

        # Tax Percentage Method for Single, taxable pay over $962, under $1346
        wh = -27.58

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('NJ'),
                                        nj_njw4_sit_filing_status='married_separate',
                                        nj_njw4_sit_allowances=3,
                                        state_income_tax_additional_withholding=0.0,
                                        #nj_njw4_sit_rate_table='B',
                                        schedule_pay='weekly')

        self.assertEqual(contract.schedule_pay, 'weekly')

        self._log('2019 New Jersey tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_SIT'], wh)


    def test_2019_taxes_to_the_limits(self):
        salary = 30000.00

        # Tax Percentage Method for Single, taxable pay over $18750, under 125000
        wh = -1467.51

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('NJ'),
                                        nj_njw4_sit_filing_status='married_joint',
                                        nj_njw4_sit_allowances=3,
                                        state_income_tax_additional_withholding=0.0,
                                        # nj_njw4_sit_rate_table='B',
                                        schedule_pay='quarterly')

        self.assertEqual(contract.schedule_pay, 'quarterly')

        self._log('2019 New Jersey tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-03-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_SIT'], wh)
