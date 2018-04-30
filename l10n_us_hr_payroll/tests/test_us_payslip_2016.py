from .test_us_payslip import TestUsPayslip, process_payslip

from openerp.addons.l10n_us_hr_payroll.l10n_us_hr_payroll import USHrContract


class TestUsPayslip2016(TestUsPayslip):
    FUTA_RATE_NORMAL_2016 = 0.6
    FUTA_RATE_BASIC_2016 = 6.0
    FUTA_RATE_EXEMPT_2016 = 0.0


    ###
    #   2016 Taxes and Rates
    ###

    def test_2016_taxes(self):
        # salary is high so that second payslip runs over max
        # social security salary
        salary = 80000.0

        ## tax rates
        FICA_SS = -0.062
        FICA_M = -0.0145
        FUTA = -self.FUTA_RATE_NORMAL_2016 / 100.0
        FICA_M_ADD = -0.009

        ## tax maximums
        FICA_SS_MAX_WAGE = 118500.0
        FICA_M_MAX_WAGE = self.float_info.max
        FICA_M_ADD_START_WAGE = 200000.0
        FUTA_MAX_WAGE = 7000.0

        employee = self._createEmployee()

        contract = self._createContract(employee, salary)

        self._log('2016 tax first payslip:')
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FICA_EMP_SS_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_SS'], cats['FICA_EMP_SS_WAGES'] * FICA_SS)
        self.assertPayrollEqual(cats['FICA_EMP_M_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_M'], cats['FICA_EMP_M_WAGES'] * FICA_M)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD_WAGES'], 0.0)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD'], 0.0)
        self.assertPayrollEqual(cats['FICA_COMP_SS'], cats['FICA_EMP_SS'])
        self.assertPayrollEqual(cats['FICA_COMP_M'], cats['FICA_EMP_M'])
        self.assertPayrollEqual(cats['FUTA_WAGES'], FUTA_MAX_WAGE)
        self.assertPayrollEqual(cats['FUTA'], cats['FUTA_WAGES'] * FUTA)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums for FICA Social Security Wages

        remaining_ss_wages = FICA_SS_MAX_WAGE - salary if (FICA_SS_MAX_WAGE - 2 * salary < salary) else salary
        remaining_m_wages = FICA_M_MAX_WAGE - salary if (FICA_M_MAX_WAGE - 2 * salary < salary) else salary

        self._log('2016 tax second payslip:')
        payslip = self._createPayslip(employee, '2016-02-01', '2016-02-29')  # 2016 is a leap year

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FICA_EMP_SS_WAGES'], remaining_ss_wages)
        self.assertPayrollEqual(cats['FICA_EMP_SS'], cats['FICA_EMP_SS_WAGES'] * FICA_SS)
        self.assertPayrollEqual(cats['FICA_EMP_M_WAGES'], remaining_m_wages)
        self.assertPayrollEqual(cats['FICA_EMP_M'], cats['FICA_EMP_M_WAGES'] * FICA_M)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD_WAGES'], 0.0)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD'], 0.0)
        self.assertPayrollEqual(cats['FICA_COMP_SS'], cats['FICA_EMP_SS'])
        self.assertPayrollEqual(cats['FICA_COMP_M'], cats['FICA_EMP_M'])
        self.assertPayrollEqual(cats['FUTA_WAGES'], 0)
        self.assertPayrollEqual(cats['FUTA'], 0)

        process_payslip(payslip)

        # Make a new payslip, this one will have reached Medicare Additional (employee only)

        self._log('2016 tax third payslip:')
        payslip = self._createPayslip(employee, '2016-03-01', '2016-03-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FICA_EMP_M_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD_WAGES'], FICA_M_ADD_START_WAGE - (salary * 2))  # aka 40k
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD'], cats['FICA_EMP_M_ADD_WAGES'] * FICA_M_ADD)

        process_payslip(payslip)

        # Make a new payslip, this one will have all salary as Medicare Additional

        self._log('2016 tax fourth payslip:')
        payslip = self._createPayslip(employee, '2016-04-01', '2016-04-30')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FICA_EMP_M_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD'], cats['FICA_EMP_M_ADD_WAGES'] * FICA_M_ADD)

        process_payslip(payslip)


    def test_2016_fed_income_withholding_single(self):
        salary = 6000.00
        schedule_pay = 'monthly'
        w4_allowances = 3
        w4_allowance_amt = 337.50 * w4_allowances
        adjusted_salary = salary - w4_allowance_amt  # should be 4987.50, but would work over a wide value for the rate
        ###
        # Single MONTHLY form Publication 15
        expected_withholding = self.float_round(-(431.95 + ((adjusted_salary - 3325) * 0.25)), self.payroll_digits)

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, schedule_pay, w4_allowances, 'single')

        self._log('2016 fed income single payslip: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FED_INC_WITHHOLD'], expected_withholding)


    def test_2016_fed_income_withholding_married_as_single(self):
        salary = 500.00
        schedule_pay = 'weekly'
        w4_allowances = 1
        w4_allowance_amt = 77.90 * w4_allowances
        adjusted_salary = salary - w4_allowance_amt  # should be 422.10, but would work over a wide value for the rate
        ###
        # Single MONTHLY form Publication 15
        expected_withholding = self.float_round(-(17.90 + ((adjusted_salary - 222) * 0.15)), self.payroll_digits)

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, schedule_pay, w4_allowances, 'married_as_single')

        self._log('2016 fed income married_as_single payslip: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FED_INC_WITHHOLD'], expected_withholding)


    def test_2016_fed_income_withholding_married(self):
        salary = 14000.00
        schedule_pay = 'bi-weekly'
        w4_allowances = 2
        w4_allowance_amt = 155.80 * w4_allowances
        adjusted_salary = salary - w4_allowance_amt  # should be 1368.84, but would work over a wide value for the rate
        ###
        # Single MONTHLY form Publication 15
        expected_withholding = self.float_round(-(1992.05 + ((adjusted_salary - 9231) * 0.33)), self.payroll_digits)

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, schedule_pay, w4_allowances, 'married')

        self._log('2016 fed income married payslip: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FED_INC_WITHHOLD'], expected_withholding)


    def test_2016_taxes_with_external(self):
        ## tax rates
        FICA_SS = -0.062
        FICA_M = -0.0145
        FUTA = -self.FUTA_RATE_NORMAL_2016 / 100.0
        FICA_M_ADD = -0.009

        ## tax maximums
        FICA_SS_MAX_WAGE = 118500.0
        FICA_M_MAX_WAGE = self.float_info.max
        FICA_M_ADD_START_WAGE = 200000.0
        FUTA_MAX_WAGE = 7000.0

        # social security salary
        salary = FICA_M_ADD_START_WAGE
        external_wages = 6000.0

        employee = self._createEmployee()

        contract = self._createContract(employee, salary, external_wages=external_wages)

        self._log('2016 tax first payslip:')
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FICA_EMP_SS_WAGES'], FICA_SS_MAX_WAGE - external_wages)
        self.assertPayrollEqual(cats['FICA_EMP_SS'], cats['FICA_EMP_SS_WAGES'] * FICA_SS)
        self.assertPayrollEqual(cats['FICA_EMP_M_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_M'], cats['FICA_EMP_M_WAGES'] * FICA_M)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD_WAGES'], 0.0)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD'], cats['FICA_EMP_M_ADD_WAGES'] * FICA_M_ADD)
        self.assertPayrollEqual(cats['FICA_COMP_SS'], cats['FICA_EMP_SS'])
        self.assertPayrollEqual(cats['FICA_COMP_M'], cats['FICA_EMP_M'])
        self.assertPayrollEqual(cats['FUTA_WAGES'], FUTA_MAX_WAGE - external_wages)
        self.assertPayrollEqual(cats['FUTA'], cats['FUTA_WAGES'] * FUTA)


    def test_2016_taxes_with_full_futa(self):
        ## tax rates
        FICA_SS = -0.062
        FICA_M = -0.0145
        FUTA = -self.FUTA_RATE_BASIC_2016 / 100.0  # because of state exemption
        FICA_M_ADD = -0.009

        ## tax maximums
        FICA_SS_MAX_WAGE = 118500.0
        FICA_M_MAX_WAGE = self.float_info.max
        FICA_M_ADD_START_WAGE = 200000.0
        FUTA_MAX_WAGE = 7000.0

        # social security salary
        salary = FICA_M_ADD_START_WAGE

        employee = self._createEmployee()

        contract = self._createContract(employee, salary, futa_type=USHrContract.FUTA_TYPE_BASIC)

        self._log('2016 tax first payslip:')
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FICA_EMP_SS_WAGES'], FICA_SS_MAX_WAGE)
        self.assertPayrollEqual(cats['FICA_EMP_SS'], cats['FICA_EMP_SS_WAGES'] * FICA_SS)
        self.assertPayrollEqual(cats['FICA_EMP_M_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_M'], cats['FICA_EMP_M_WAGES'] * FICA_M)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD_WAGES'], 0.0)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD'], cats['FICA_EMP_M_ADD_WAGES'] * FICA_M_ADD)
        self.assertPayrollEqual(cats['FICA_COMP_SS'], cats['FICA_EMP_SS'])
        self.assertPayrollEqual(cats['FICA_COMP_M'], cats['FICA_EMP_M'])
        self.assertPayrollEqual(cats['FUTA_WAGES'], FUTA_MAX_WAGE)
        self.assertPayrollEqual(cats['FUTA'], cats['FUTA_WAGES'] * FUTA)


    def test_2016_taxes_with_futa_exempt(self):
        ## tax rates
        FICA_SS = -0.062
        FICA_M = -0.0145
        FUTA = self.FUTA_RATE_EXEMPT_2016  # because of exemption
        FICA_M_ADD = -0.009

        ## tax maximums
        FICA_SS_MAX_WAGE = 118500.0
        FICA_M_MAX_WAGE = self.float_info.max
        FICA_M_ADD_START_WAGE = 200000.0
        FUTA_MAX_WAGE = 7000.0

        # social security salary
        salary = FICA_M_ADD_START_WAGE

        employee = self._createEmployee()

        contract = self._createContract(employee, salary, futa_type=USHrContract.FUTA_TYPE_EXEMPT)

        self._log('2016 tax first payslip:')
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FICA_EMP_SS_WAGES'], FICA_SS_MAX_WAGE)
        self.assertPayrollEqual(cats['FICA_EMP_SS'], cats['FICA_EMP_SS_WAGES'] * FICA_SS)
        self.assertPayrollEqual(cats['FICA_EMP_M_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_M'], cats['FICA_EMP_M_WAGES'] * FICA_M)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD_WAGES'], 0.0)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD'], cats['FICA_EMP_M_ADD_WAGES'] * FICA_M_ADD)
        self.assertPayrollEqual(cats['FICA_COMP_SS'], cats['FICA_EMP_SS'])
        self.assertPayrollEqual(cats['FICA_COMP_M'], cats['FICA_EMP_M'])

        FUTA_WAGES = 0.0
        if 'FUTA_WAGES' in cats:
            FUTA_WAGES = cats['FUTA_WAGES']
        FUTA = 0.0
        if 'FUTA' in cats:
            FUTA = cats['FUTA']
        self.assertPayrollEqual(FUTA_WAGES, 0.0)
        self.assertPayrollEqual(FUTA, FUTA_WAGES * FUTA)


    def test_2016_fed_income_withholding_nonresident_alien(self):
        salary = 3500.00
        schedule_pay = 'quarterly'
        w4_allowances = 1
        w4_allowance_amt = 1012.50 * w4_allowances
        nra_adjustment = 562.50  # for quarterly
        adjusted_salary = salary - w4_allowance_amt + nra_adjustment  # 3050

        ###
        # Single QUARTERLY form Publication 15
        expected_withholding = self.float_round(-(231.80 + ((adjusted_salary - 2881) * 0.15)), self.payroll_digits)

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, schedule_pay, w4_allowances, 'single',
                                        w4_is_nonresident_alien=True)

        self._log('2016 fed income single payslip nonresident alien: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FED_INC_WITHHOLD'], expected_withholding)


    def test_2016_fed_income_additional_withholding(self):
        salary = 50000.00
        schedule_pay = 'annually'
        w4_additional_withholding = 5000.0
        w4_allowances = 2
        w4_allowance_amt = 4050.0 * w4_allowances
        adjusted_salary = salary - w4_allowance_amt  # 41900

        ###
        # Single ANNUAL form Publication 15
        expected_withholding = self.float_round(-((1855 + ((adjusted_salary - 27100) * 0.15)) + w4_additional_withholding),
                                           self.payroll_digits)

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, schedule_pay, w4_allowances, 'married',
                                        w4_additional_withholding=w4_additional_withholding)

        self._log('2016 fed income married payslip additional withholding: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FED_INC_WITHHOLD'], expected_withholding)


    def test_2016_taxes_with_w4_exempt(self):
        salary = 6000.0
        schedule_pay = 'bi-weekly'
        w4_allowances = 0
        employee = self._createEmployee()
        contract = self._createContract(employee, salary, schedule_pay, w4_allowances, '')

        self._log('2016 tax w4 exempt payslip:')
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        FED_INC_WITHHOLD = 0.0
        if 'FED_INC_WITHHOLD' in cats:
            FED_INC_WITHHOLD = cats['FED_INC_WITHHOLD']
        self.assertPayrollEqual(FED_INC_WITHHOLD, 0.0)
