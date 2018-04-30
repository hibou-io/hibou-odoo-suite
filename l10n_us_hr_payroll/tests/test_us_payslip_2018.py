from .test_us_payslip import TestUsPayslip, process_payslip

from odoo.addons.l10n_us_hr_payroll.l10n_us_hr_payroll import USHrContract

from sys import float_info


class TestUsPayslip2018(TestUsPayslip):
    # FUTA Constants
    FUTA_RATE_NORMAL = 0.6
    FUTA_RATE_BASIC = 6.0
    FUTA_RATE_EXEMPT = 0.0

    # Wage caps
    FICA_SS_MAX_WAGE = 128400.0
    FICA_M_MAX_WAGE = float_info.max
    FICA_M_ADD_START_WAGE = 200000.0
    FUTA_MAX_WAGE = 7000.0

    # Rates
    FICA_SS = 6.2 / -100.0
    FICA_M = 1.45 / -100.0
    FUTA = FUTA_RATE_NORMAL / -100.0
    FICA_M_ADD = 0.9 / -100.0

    ###
    #   2018 Taxes and Rates
    ###

    def test_2018_taxes(self):
        # salary is high so that second payslip runs over max
        # social security salary
        salary = 80000.0

        employee = self._createEmployee()

        self._createContract(employee, salary)

        self._log('2017 tax last slip')
        payslip = self._createPayslip(employee, '2017-12-01', '2017-12-31')
        payslip.compute_sheet()
        process_payslip(payslip)

        self._log('2018 tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FICA_EMP_SS_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_SS'], cats['FICA_EMP_SS_WAGES'] * self.FICA_SS)
        self.assertPayrollEqual(cats['FICA_EMP_M_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_M'], cats['FICA_EMP_M_WAGES'] * self.FICA_M)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD_WAGES'], 0.0)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD'], 0.0)
        self.assertPayrollEqual(cats['FICA_COMP_SS'], cats['FICA_EMP_SS'])
        self.assertPayrollEqual(cats['FICA_COMP_M'], cats['FICA_EMP_M'])
        self.assertPayrollEqual(cats['FUTA_WAGES'], self.FUTA_MAX_WAGE)
        self.assertPayrollEqual(cats['FUTA'], cats['FUTA_WAGES'] * self.FUTA)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums for FICA Social Security Wages

        remaining_ss_wages = self.FICA_SS_MAX_WAGE - salary if (self.FICA_SS_MAX_WAGE - 2 * salary < salary) else salary
        remaining_m_wages = self.FICA_M_MAX_WAGE - salary if (self.FICA_M_MAX_WAGE - 2 * salary < salary) else salary

        self._log('2018 tax second payslip:')
        payslip = self._createPayslip(employee, '2018-02-01', '2018-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FICA_EMP_SS_WAGES'], remaining_ss_wages)
        self.assertPayrollEqual(cats['FICA_EMP_SS'], cats['FICA_EMP_SS_WAGES'] * self.FICA_SS)
        self.assertPayrollEqual(cats['FICA_EMP_M_WAGES'], remaining_m_wages)
        self.assertPayrollEqual(cats['FICA_EMP_M'], cats['FICA_EMP_M_WAGES'] * self.FICA_M)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD_WAGES'], 0.0)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD'], 0.0)
        self.assertPayrollEqual(cats['FICA_COMP_SS'], cats['FICA_EMP_SS'])
        self.assertPayrollEqual(cats['FICA_COMP_M'], cats['FICA_EMP_M'])
        self.assertPayrollEqual(cats['FUTA_WAGES'], 0)
        self.assertPayrollEqual(cats['FUTA'], 0)

        process_payslip(payslip)

        # Make a new payslip, this one will have reached Medicare Additional (employee only)

        self._log('2018 tax third payslip:')
        payslip = self._createPayslip(employee, '2018-03-01', '2018-03-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FICA_EMP_M_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD_WAGES'], self.FICA_M_ADD_START_WAGE - (salary * 2))  # aka 40k
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD'], cats['FICA_EMP_M_ADD_WAGES'] * self.FICA_M_ADD)

        process_payslip(payslip)

        # Make a new payslip, this one will have all salary as Medicare Additional

        self._log('2018 tax fourth payslip:')
        payslip = self._createPayslip(employee, '2018-04-01', '2018-04-30')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FICA_EMP_M_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD'], cats['FICA_EMP_M_ADD_WAGES'] * self.FICA_M_ADD)

        process_payslip(payslip)

    def test_2018_fed_income_withholding_single(self):
        salary = 6000.00
        schedule_pay = 'monthly'
        w4_allowances = 3
        w4_allowance_amt = 345.80 * w4_allowances
        adjusted_salary = salary - w4_allowance_amt  # should be 4962.60, but would work over a wide value for the rate
        ###
        # Single MONTHLY form Publication 15
        expected_withholding = self.float_round(-(371.12 + ((adjusted_salary - 3533) * 0.22)), self.payroll_digits)

        employee = self._createEmployee()
        self._createContract(employee, salary, schedule_pay, w4_allowances, 'single')

        self._log('2018 fed income single payslip: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FED_INC_WITHHOLD'], expected_withholding)

    def test_2018_fed_income_withholding_married_as_single(self):
        salary = 500.00
        schedule_pay = 'weekly'
        w4_allowances = 1
        w4_allowance_amt = 79.80 * w4_allowances
        adjusted_salary = salary - w4_allowance_amt  # should be 420.50, but would work over a wide value for the rate
        ###
        # Single MONTHLY form Publication 15
        expected_withholding = self.float_round(-(18.30 + ((adjusted_salary - 254) * 0.12)), self.payroll_digits)

        employee = self._createEmployee()
        self._createContract(employee, salary, schedule_pay, w4_allowances, 'married_as_single')

        self._log('2018 fed income married_as_single payslip: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FED_INC_WITHHOLD'], expected_withholding)

    def test_2018_fed_income_withholding_married(self):
        salary = 14000.00
        schedule_pay = 'bi-weekly'
        w4_allowances = 2
        w4_allowance_amt = 159.60 * w4_allowances
        adjusted_salary = salary - w4_allowance_amt  # should be 13680.80, but would work over a wide value for the rate
        ###
        # Single MONTHLY form Publication 15
        expected_withholding = self.float_round(-(2468.56 + ((adjusted_salary - 12560) * 0.32)), self.payroll_digits)

        employee = self._createEmployee()
        self._createContract(employee, salary, schedule_pay, w4_allowances, 'married')

        self._log('2018 fed income married payslip: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FED_INC_WITHHOLD'], expected_withholding)

    def test_2018_taxes_with_external(self):

        # social security salary
        salary = self.FICA_M_ADD_START_WAGE
        external_wages = 6000.0

        employee = self._createEmployee()

        self._createContract(employee, salary, external_wages=external_wages)

        self._log('2018 tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FICA_EMP_SS_WAGES'], self.FICA_SS_MAX_WAGE - external_wages)
        self.assertPayrollEqual(cats['FICA_EMP_SS'], cats['FICA_EMP_SS_WAGES'] * self.FICA_SS)
        self.assertPayrollEqual(cats['FICA_EMP_M_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_M'], cats['FICA_EMP_M_WAGES'] * self.FICA_M)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD_WAGES'], 0.0)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD'], cats['FICA_EMP_M_ADD_WAGES'] * self.FICA_M_ADD)
        self.assertPayrollEqual(cats['FICA_COMP_SS'], cats['FICA_EMP_SS'])
        self.assertPayrollEqual(cats['FICA_COMP_M'], cats['FICA_EMP_M'])
        self.assertPayrollEqual(cats['FUTA_WAGES'], self.FUTA_MAX_WAGE - external_wages)
        self.assertPayrollEqual(cats['FUTA'], cats['FUTA_WAGES'] * self.FUTA)

    def test_2018_taxes_with_full_futa(self):
        futa_rate = self.FUTA_RATE_BASIC / -100.0
        # social security salary
        salary = self.FICA_M_ADD_START_WAGE

        employee = self._createEmployee()

        self._createContract(employee, salary, futa_type=USHrContract.FUTA_TYPE_BASIC)

        self._log('2018 tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FICA_EMP_SS_WAGES'], self.FICA_SS_MAX_WAGE)
        self.assertPayrollEqual(cats['FICA_EMP_SS'], cats['FICA_EMP_SS_WAGES'] * self.FICA_SS)
        self.assertPayrollEqual(cats['FICA_EMP_M_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_M'], cats['FICA_EMP_M_WAGES'] * self.FICA_M)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD_WAGES'], 0.0)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD'], cats['FICA_EMP_M_ADD_WAGES'] * self.FICA_M_ADD)
        self.assertPayrollEqual(cats['FICA_COMP_SS'], cats['FICA_EMP_SS'])
        self.assertPayrollEqual(cats['FICA_COMP_M'], cats['FICA_EMP_M'])
        self.assertPayrollEqual(cats['FUTA_WAGES'], self.FUTA_MAX_WAGE)
        self.assertPayrollEqual(cats['FUTA'], cats['FUTA_WAGES'] * futa_rate)

    def test_2018_taxes_with_futa_exempt(self):
        futa_rate = self.FUTA_RATE_EXEMPT / -100.0  # because of exemption

        # social security salary
        salary = self.FICA_M_ADD_START_WAGE

        employee = self._createEmployee()

        self._createContract(employee, salary, futa_type=USHrContract.FUTA_TYPE_EXEMPT)

        self._log('2018 tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FICA_EMP_SS_WAGES'], self.FICA_SS_MAX_WAGE)
        self.assertPayrollEqual(cats['FICA_EMP_SS'], cats['FICA_EMP_SS_WAGES'] * self.FICA_SS)
        self.assertPayrollEqual(cats['FICA_EMP_M_WAGES'], salary)
        self.assertPayrollEqual(cats['FICA_EMP_M'], cats['FICA_EMP_M_WAGES'] * self.FICA_M)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD_WAGES'], 0.0)
        self.assertPayrollEqual(cats['FICA_EMP_M_ADD'], cats['FICA_EMP_M_ADD_WAGES'] * self.FICA_M_ADD)
        self.assertPayrollEqual(cats['FICA_COMP_SS'], cats['FICA_EMP_SS'])
        self.assertPayrollEqual(cats['FICA_COMP_M'], cats['FICA_EMP_M'])

        futa_wages = 0.0
        if 'FUTA_WAGES' in cats:
            futa_wages = cats['FUTA_WAGES']
        futa = 0.0
        if 'FUTA' in cats:
            futa = cats['FUTA']
        self.assertPayrollEqual(futa_wages, 0.0)
        self.assertPayrollEqual(futa, futa_wages * futa_rate)

    def test_2018_fed_income_withholding_nonresident_alien(self):
        salary = 3500.00
        schedule_pay = 'quarterly'
        w4_allowances = 1
        w4_allowance_amt = 1037.50 * w4_allowances
        nra_adjustment = 1962.50  # for quarterly
        adjusted_salary = salary - w4_allowance_amt + nra_adjustment  # 4425

        ###
        # Single QUARTERLY form Publication 15
        expected_withholding = self.float_round(-(238.10 + ((adjusted_salary - 3306) * 0.12)), self.payroll_digits)

        employee = self._createEmployee()
        self._createContract(employee, salary, schedule_pay, w4_allowances, 'single',
                             w4_is_nonresident_alien=True)

        self._log('2018 fed income single payslip nonresident alien: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FED_INC_WITHHOLD'], expected_withholding)

    def test_2018_fed_income_additional_withholding(self):
        salary = 50000.00
        schedule_pay = 'annually'
        w4_additional_withholding = 5000.0
        w4_allowances = 2
        w4_allowance_amt = 4150.00 * w4_allowances
        adjusted_salary = salary - w4_allowance_amt  # 41700

        ###
        # Single ANNUAL form Publication 15
        expected_withholding = \
            self.float_round(-((1905.00 + ((adjusted_salary - 30600) * 0.12)) + w4_additional_withholding),
                             self.payroll_digits)

        employee = self._createEmployee()
        self._createContract(employee, salary, schedule_pay, w4_allowances, 'married',
                             w4_additional_withholding=w4_additional_withholding)

        self._log('2018 fed income married payslip additional withholding: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FED_INC_WITHHOLD'], expected_withholding)

    def test_2018_taxes_with_w4_exempt(self):
        salary = 6000.0
        schedule_pay = 'bi-weekly'
        w4_allowances = 0
        employee = self._createEmployee()
        self._createContract(employee, salary, schedule_pay, w4_allowances, '')

        self._log('2018 tax w4 exempt payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        fed_inc_withhold = 0.0
        if 'FED_INC_WITHHOLD' in cats:
            fed_inc_withhold = cats['FED_INC_WITHHOLD']
        self.assertPayrollEqual(fed_inc_withhold, 0.0)
