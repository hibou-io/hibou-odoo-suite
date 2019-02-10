from .test_us_payslip import TestUsPayslip, process_payslip

from odoo.addons.l10n_us_hr_payroll.models.l10n_us_hr_payroll import USHrContract

from sys import float_info


class TestUsPayslip2019(TestUsPayslip):
    # FUTA Constants
    FUTA_RATE_NORMAL = 0.6
    FUTA_RATE_BASIC = 6.0
    FUTA_RATE_EXEMPT = 0.0

    # Wage caps
    FICA_SS_MAX_WAGE = 132900.0
    FICA_M_MAX_WAGE = float_info.max
    FICA_M_ADD_START_WAGE = 200000.0
    FUTA_MAX_WAGE = 7000.0

    # Rates
    FICA_SS = 6.2 / -100.0
    FICA_M = 1.45 / -100.0
    FUTA = FUTA_RATE_NORMAL / -100.0
    FICA_M_ADD = 0.9 / -100.0

    ###
    #   2019 Taxes and Rates
    ###

    def test_2019_taxes(self):
        # salary is high so that second payslip runs over max
        # social security salary
        salary = 80000.0

        employee = self._createEmployee()

        self._createContract(employee, salary)

        self._log('2018 tax last slip')
        payslip = self._createPayslip(employee, '2018-12-01', '2018-12-31')
        payslip.compute_sheet()
        process_payslip(payslip)

        self._log('2019 tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_FICA_SS'], salary)
        self.assertPayrollEqual(cats['EE_US_FICA_SS'], cats['WAGE_US_FICA_SS'] * self.FICA_SS)
        self.assertPayrollEqual(cats['WAGE_US_FICA_M'], salary)
        self.assertPayrollEqual(cats['EE_US_FICA_M'], cats['WAGE_US_FICA_M'] * self.FICA_M)
        self.assertPayrollEqual(cats['WAGE_US_FICA_M_ADD'], 0.0)
        self.assertPayrollEqual(cats['EE_US_FICA_M_ADD'], 0.0)
        self.assertPayrollEqual(cats['ER_US_FICA_SS'], cats['EE_US_FICA_SS'])
        self.assertPayrollEqual(cats['ER_US_FICA_M'], cats['EE_US_FICA_M'])
        self.assertPayrollEqual(cats['WAGE_US_FUTA'], self.FUTA_MAX_WAGE)
        self.assertPayrollEqual(cats['ER_US_FUTA'], cats['WAGE_US_FUTA'] * self.FUTA)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums for FICA Social Security Wages

        remaining_ss_wages = self.FICA_SS_MAX_WAGE - salary if (self.FICA_SS_MAX_WAGE - 2 * salary < salary) else salary
        remaining_m_wages = self.FICA_M_MAX_WAGE - salary if (self.FICA_M_MAX_WAGE - 2 * salary < salary) else salary

        self._log('2019 tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_FICA_SS'], remaining_ss_wages)
        self.assertPayrollEqual(cats['EE_US_FICA_SS'], cats['WAGE_US_FICA_SS'] * self.FICA_SS)
        self.assertPayrollEqual(cats['WAGE_US_FICA_M'], remaining_m_wages)
        self.assertPayrollEqual(cats['EE_US_FICA_M'], cats['WAGE_US_FICA_M'] * self.FICA_M)
        self.assertPayrollEqual(cats['WAGE_US_FICA_M_ADD'], 0.0)
        self.assertPayrollEqual(cats['EE_US_FICA_M_ADD'], 0.0)
        self.assertPayrollEqual(cats['ER_US_FICA_SS'], cats['EE_US_FICA_SS'])
        self.assertPayrollEqual(cats['ER_US_FICA_M'], cats['EE_US_FICA_M'])
        self.assertPayrollEqual(cats['WAGE_US_FUTA'], 0)
        self.assertPayrollEqual(cats['ER_US_FUTA'], 0)

        process_payslip(payslip)

        # Make a new payslip, this one will have reached Medicare Additional (employee only)

        self._log('2019 tax third payslip:')
        payslip = self._createPayslip(employee, '2019-03-01', '2019-03-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_FICA_M'], salary)
        self.assertPayrollEqual(cats['WAGE_US_FICA_M_ADD'], self.FICA_M_ADD_START_WAGE - (salary * 2))  # aka 40k
        self.assertPayrollEqual(cats['EE_US_FICA_M_ADD'], cats['WAGE_US_FICA_M_ADD'] * self.FICA_M_ADD)

        process_payslip(payslip)

        # Make a new payslip, this one will have all salary as Medicare Additional

        self._log('2019 tax fourth payslip:')
        payslip = self._createPayslip(employee, '2019-04-01', '2019-04-30')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_FICA_M'], salary)
        self.assertPayrollEqual(cats['WAGE_US_FICA_M_ADD'], salary)
        self.assertPayrollEqual(cats['EE_US_FICA_M_ADD'], cats['WAGE_US_FICA_M_ADD'] * self.FICA_M_ADD)

        process_payslip(payslip)

    def test_2019_fed_income_withholding_single(self):
        salary = 6000.00
        schedule_pay = 'monthly'
        w4_allowances = 3
        w4_allowance_amt = 350.00 * w4_allowances
        adjusted_salary = salary - w4_allowance_amt  # should be 4962.60, but would work over a wide value for the rate
        ###
        # Single MONTHLY form Publication 15
        expected_withholding = self.float_round(-(378.52 + ((adjusted_salary - 3606) * 0.22)), self.payroll_digits)

        employee = self._createEmployee()
        self._createContract(employee, salary, schedule_pay, w4_allowances, 'single')

        self._log('2019 fed income single payslip: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_FED_INC_WITHHOLD'], expected_withholding)

    def test_2019_fed_income_withholding_married_as_single(self):
        salary = 500.00
        schedule_pay = 'weekly'
        w4_allowances = 1
        w4_allowance_amt = 80.80 * w4_allowances
        adjusted_salary = salary - w4_allowance_amt  # should be 420.50, but would work over a wide value for the rate
        ###
        # Single MONTHLY form Publication 15
        expected_withholding = self.float_round(-(18.70 + ((adjusted_salary - 260) * 0.12)), self.payroll_digits)

        employee = self._createEmployee()
        self._createContract(employee, salary, schedule_pay, w4_allowances, 'married_as_single')

        self._log('2019 fed income married_as_single payslip: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_FED_INC_WITHHOLD'], expected_withholding)

    def test_2019_fed_income_withholding_married(self):
        salary = 14000.00
        schedule_pay = 'bi-weekly'
        w4_allowances = 2
        w4_allowance_amt = 161.50 * w4_allowances
        adjusted_salary = salary - w4_allowance_amt  # should be 13680.80, but would work over a wide value for the rate
        ###
        # Single MONTHLY form Publication 15
        expected_withholding = self.float_round(-(2519.06 + ((adjusted_salary - 12817) * 0.32)), self.payroll_digits)

        employee = self._createEmployee()
        self._createContract(employee, salary, schedule_pay, w4_allowances, 'married')

        self._log('2019 fed income married payslip: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_FED_INC_WITHHOLD'], expected_withholding)

    def test_2019_taxes_with_external(self):

        # social security salary
        salary = self.FICA_M_ADD_START_WAGE
        external_wages = 6000.0

        employee = self._createEmployee()

        self._createContract(employee, salary, external_wages=external_wages)

        self._log('2019 tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_FICA_SS'], self.FICA_SS_MAX_WAGE - external_wages)
        self.assertPayrollEqual(cats['EE_US_FICA_SS'], cats['WAGE_US_FICA_SS'] * self.FICA_SS)
        self.assertPayrollEqual(cats['WAGE_US_FICA_M'], salary)
        self.assertPayrollEqual(cats['EE_US_FICA_M'], cats['WAGE_US_FICA_M'] * self.FICA_M)
        self.assertPayrollEqual(cats['WAGE_US_FICA_M_ADD'], 0.0)
        self.assertPayrollEqual(cats['EE_US_FICA_M_ADD'], cats['WAGE_US_FICA_M_ADD'] * self.FICA_M_ADD)
        self.assertPayrollEqual(cats['ER_US_FICA_SS'], cats['EE_US_FICA_SS'])
        self.assertPayrollEqual(cats['ER_US_FICA_M'], cats['EE_US_FICA_M'])
        self.assertPayrollEqual(cats['WAGE_US_FUTA'], self.FUTA_MAX_WAGE - external_wages)
        self.assertPayrollEqual(cats['ER_US_FUTA'], cats['WAGE_US_FUTA'] * self.FUTA)

    def test_2019_taxes_with_full_futa(self):
        futa_rate = self.FUTA_RATE_BASIC / -100.0
        # social security salary
        salary = self.FICA_M_ADD_START_WAGE

        employee = self._createEmployee()

        self._createContract(employee, salary, futa_type=USHrContract.FUTA_TYPE_BASIC)

        self._log('2019 tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_FICA_SS'], self.FICA_SS_MAX_WAGE)
        self.assertPayrollEqual(cats['EE_US_FICA_SS'], cats['WAGE_US_FICA_SS'] * self.FICA_SS)
        self.assertPayrollEqual(cats['WAGE_US_FICA_M'], salary)
        self.assertPayrollEqual(cats['EE_US_FICA_M'], cats['WAGE_US_FICA_M'] * self.FICA_M)
        self.assertPayrollEqual(cats['WAGE_US_FICA_M_ADD'], 0.0)
        self.assertPayrollEqual(cats['EE_US_FICA_M_ADD'], cats['WAGE_US_FICA_M_ADD'] * self.FICA_M_ADD)
        self.assertPayrollEqual(cats['ER_US_FICA_SS'], cats['EE_US_FICA_SS'])
        self.assertPayrollEqual(cats['ER_US_FICA_M'], cats['EE_US_FICA_M'])
        self.assertPayrollEqual(cats['WAGE_US_FUTA'], self.FUTA_MAX_WAGE)
        self.assertPayrollEqual(cats['ER_US_FUTA'], cats['WAGE_US_FUTA'] * futa_rate)

    def test_2019_taxes_with_futa_exempt(self):
        futa_rate = self.FUTA_RATE_EXEMPT / -100.0  # because of exemption

        # social security salary
        salary = self.FICA_M_ADD_START_WAGE

        employee = self._createEmployee()

        self._createContract(employee, salary, futa_type=USHrContract.FUTA_TYPE_EXEMPT)

        self._log('2019 tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_FICA_SS'], self.FICA_SS_MAX_WAGE)
        self.assertPayrollEqual(cats['EE_US_FICA_SS'], cats['WAGE_US_FICA_SS'] * self.FICA_SS)
        self.assertPayrollEqual(cats['WAGE_US_FICA_M'], salary)
        self.assertPayrollEqual(cats['EE_US_FICA_M'], cats['WAGE_US_FICA_M'] * self.FICA_M)
        self.assertPayrollEqual(cats['WAGE_US_FICA_M_ADD'], 0.0)
        self.assertPayrollEqual(cats['EE_US_FICA_M_ADD'], cats['WAGE_US_FICA_M_ADD'] * self.FICA_M_ADD)
        self.assertPayrollEqual(cats['ER_US_FICA_SS'], cats['EE_US_FICA_SS'])
        self.assertPayrollEqual(cats['ER_US_FICA_M'], cats['EE_US_FICA_M'])

        futa_wages = 0.0
        if 'WAGE_US_FUTA' in cats:
            futa_wages = cats['WAGE_US_FUTA']
        futa = 0.0
        if 'ER_US_FUTA' in cats:
            futa = cats['ER_US_FUTA']
        self.assertPayrollEqual(futa_wages, 0.0)
        self.assertPayrollEqual(futa, futa_wages * futa_rate)

    def test_2019_fed_income_withholding_nonresident_alien(self):
        salary = 3500.00
        schedule_pay = 'quarterly'
        w4_allowances = 1
        w4_allowance_amt = 1050.0 * w4_allowances
        nra_adjustment = 2000.0  # for quarterly
        adjusted_salary = salary - w4_allowance_amt + nra_adjustment  # 4425

        ###
        # Single QUARTERLY form Publication 15
        expected_withholding = self.float_round(-(242.50 + ((adjusted_salary - 3375) * 0.12)), self.payroll_digits)

        employee = self._createEmployee()
        self._createContract(employee, salary, schedule_pay, w4_allowances, 'single',
                             w4_is_nonresident_alien=True)

        self._log('2019 fed income single payslip nonresident alien: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_FED_INC_WITHHOLD'], expected_withholding)

    def test_2019_fed_income_additional_withholding(self):
        salary = 50000.00
        schedule_pay = 'annually'
        w4_additional_withholding = 5000.0
        w4_allowances = 2
        w4_allowance_amt = 4200.0 * w4_allowances
        adjusted_salary = salary - w4_allowance_amt  # 41700

        ###
        # Single ANNUAL form Publication 15
        expected_withholding = \
            self.float_round(-((1940.00 + ((adjusted_salary - 31200) * 0.12)) + w4_additional_withholding),
                             self.payroll_digits)

        employee = self._createEmployee()
        self._createContract(employee, salary, schedule_pay, w4_allowances, 'married',
                             w4_additional_withholding=w4_additional_withholding)

        self._log('2019 fed income married payslip additional withholding: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_FED_INC_WITHHOLD'], expected_withholding)

    def test_2019_taxes_with_w4_exempt(self):
        salary = 6000.0
        schedule_pay = 'bi-weekly'
        w4_allowances = 0
        employee = self._createEmployee()
        self._createContract(employee, salary, schedule_pay, w4_allowances, '')

        self._log('2019 tax w4 exempt payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        fed_inc_withhold = 0.0
        if 'EE_US_FED_INC_WITHHOLD' in cats:
            fed_inc_withhold = cats['EE_US_FED_INC_WITHHOLD']
        self.assertPayrollEqual(fed_inc_withhold, 0.0)

    def test_2019_taxes_with_fica_exempt(self):
        salary = 6000.0
        schedule_pay = 'bi-weekly'
        w4_allowances = 2
        employee = self._createEmployee()
        contract = self._createContract(employee, salary, schedule_pay, w4_allowances)
        contract.fica_exempt = True

        self._log('2019 tax w4 exempt payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        ss_wages = cats.get('WAGE_US_FICA_SS', 0.0)
        med_wages = cats.get('WAGE_US_FICA_M', 0.0)
        ss = cats.get('EE_US_FICA_SS', 0.0)
        med = cats.get('EE_US_FICA_M', 0.0)
        self.assertPayrollEqual(ss_wages, 0.0)
        self.assertPayrollEqual(med_wages, 0.0)
        self.assertPayrollEqual(ss, 0.0)
        self.assertPayrollEqual(med, 0.0)
