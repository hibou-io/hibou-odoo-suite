# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip

from odoo.addons.l10n_us_hr_payroll.models.hr_contract import USHRContract

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
        self.debug = False
        # salary is high so that second payslip runs over max
        # social security salary
        salary = 80000.0

        employee = self._createEmployee()

        contract = self._createContract(employee, wage=salary)
        self._log(contract.read())

        self._log('2018 tax last slip')
        payslip = self._createPayslip(employee, '2018-12-01', '2018-12-31')
        payslip.compute_sheet()
        self._log(payslip.read())
        process_payslip(payslip)

        # Ensure amounts are there, they shouldn't be added in the next year...
        cats = self._getCategories(payslip)
        self.assertTrue(cats['ER_US_940_FUTA'], self.FUTA_MAX_WAGE * self.FUTA)

        self._log('2019 tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)
        # Employee
        self.assertPayrollEqual(rules['EE_US_941_FICA_SS'], cats['BASIC'] * self.FICA_SS)
        self.assertPayrollEqual(rules['EE_US_941_FICA_M'], cats['BASIC'] * self.FICA_M)
        self.assertPayrollEqual(rules['EE_US_941_FICA_M_ADD'], 0.0)
        # Employer
        self.assertPayrollEqual(rules['ER_US_941_FICA_SS'], rules['EE_US_941_FICA_SS'])
        self.assertPayrollEqual(rules['ER_US_941_FICA_M'], rules['EE_US_941_FICA_M'])
        self.assertTrue(cats['ER_US_940_FUTA'], self.FUTA_MAX_WAGE * self.FUTA)

        process_payslip(payslip)

        # Make a new payslip, this one will have reached Medicare Additional (employee only)
        remaining_ss_wages = self.FICA_SS_MAX_WAGE - salary if (self.FICA_SS_MAX_WAGE - 2 * salary < salary) else salary
        remaining_m_wages = self.FICA_M_MAX_WAGE - salary if (self.FICA_M_MAX_WAGE - 2 * salary < salary) else salary

        self._log('2019 tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)

        self.assertPayrollEqual(rules['EE_US_941_FICA_SS'], remaining_ss_wages * self.FICA_SS)
        self.assertPayrollEqual(rules['EE_US_941_FICA_M'], remaining_m_wages * self.FICA_M)
        self.assertPayrollEqual(rules['EE_US_941_FICA_M_ADD'], 0.0)
        self.assertPayrollEqual(cats['ER_US_940_FUTA'], 0.0)

        process_payslip(payslip)

        # Make a new payslip, this one will have reached Medicare Additional (employee only)
        self._log('2019 tax third payslip:')
        payslip = self._createPayslip(employee, '2019-03-01', '2019-03-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)

        self.assertPayrollEqual(rules['EE_US_941_FICA_M_ADD'], (self.FICA_M_ADD_START_WAGE - (salary * 2)) * self.FICA_M_ADD) # aka 40k

        process_payslip(payslip)

        # Make a new payslip, this one will have all salary as Medicare Additional

        self._log('2019 tax fourth payslip:')
        payslip = self._createPayslip(employee, '2019-04-01', '2019-04-30')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)

        self.assertPayrollEqual(rules['EE_US_941_FICA_M_ADD'], salary * self.FICA_M_ADD)

        process_payslip(payslip)

    def test_2019_fed_income_withholding_single(self):
        self.debug = False

        salary = 6000.00
        schedule_pay = 'monthly'
        w4_allowances = 3
        w4_allowance_amt = 350.00 * w4_allowances
        adjusted_salary = salary - w4_allowance_amt  # should be 4962.60, but would work over a wide value for the rate
        ###
        # Single MONTHLY form Publication 15
        expected_withholding = self.float_round(-(378.52 + ((adjusted_salary - 3606) * 0.22)), self.payroll_digits)

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        schedule_pay=schedule_pay,
                                        fed_941_fit_w4_filing_status='single',
                                        fed_941_fit_w4_allowances=w4_allowances
                                        )

        self._log('2019 fed income single payslip: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats['EE_US_941_FIT'], expected_withholding)

    def test_2019_fed_income_withholding_married_as_single(self):
        salary = 500.00
        schedule_pay = 'weekly'
        w4_allowances = 1
        w4_allowance_amt = 80.80 * w4_allowances
        adjusted_salary = salary - w4_allowance_amt  # should be 420.50, but would work over a wide value for the rate
        ###
        expected_withholding = self.float_round(-(18.70 + ((adjusted_salary - 260) * 0.12)), self.payroll_digits)

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        schedule_pay=schedule_pay,
                                        fed_941_fit_w4_filing_status='married_as_single',
                                        fed_941_fit_w4_allowances=w4_allowances,
                                        )

        self._log('2019 fed income married_as_single payslip: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats['EE_US_941_FIT'], expected_withholding)

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
        contract = self._createContract(employee,
                                        wage=salary,
                                        schedule_pay=schedule_pay,
                                        fed_941_fit_w4_filing_status='married',
                                        fed_941_fit_w4_allowances=w4_allowances
                                        )

        self._log('2019 fed income married payslip: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        # This is off by 1 penny given our new reporting of adjusted wage * computed percentage
        #self.assertPayrollEqual(cats['EE_US_941_FIT'], expected_withholding)
        self.assertTrue(abs(cats['EE_US_941_FIT'] - expected_withholding) < 0.011)

    def test_2019_taxes_with_external(self):
        # social security salary
        salary = self.FICA_M_ADD_START_WAGE
        external_wages = 6000.0

        employee = self._createEmployee()

        self._createContract(employee, wage=salary, external_wages=external_wages)

        self._log('2019 tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)
        self.assertPayrollEqual(rules['EE_US_941_FICA_SS'], (self.FICA_SS_MAX_WAGE - external_wages) * self.FICA_SS)
        self.assertPayrollEqual(rules['EE_US_941_FICA_M'], salary * self.FICA_M)
        self.assertPayrollEqual(rules['EE_US_941_FICA_M_ADD'], external_wages * self.FICA_M_ADD)
        self.assertPayrollEqual(rules['ER_US_941_FICA_SS'], rules['EE_US_941_FICA_SS'])
        self.assertPayrollEqual(rules['ER_US_941_FICA_M'], rules['EE_US_941_FICA_M'])
        self.assertPayrollEqual(cats['ER_US_940_FUTA'], (self.FUTA_MAX_WAGE - external_wages) * self.FUTA)

    def test_2019_taxes_with_full_futa(self):
        futa_rate = self.FUTA_RATE_BASIC / -100.0
        # social security salary
        salary = self.FICA_M_ADD_START_WAGE

        employee = self._createEmployee()

        self._createContract(employee, wage=salary, fed_940_type=USHRContract.FUTA_TYPE_BASIC)

        self._log('2019 tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)
        self.assertPayrollEqual(rules['EE_US_941_FICA_SS'], self.FICA_SS_MAX_WAGE * self.FICA_SS)
        self.assertPayrollEqual(rules['EE_US_941_FICA_M'], salary * self.FICA_M)
        self.assertPayrollEqual(rules['EE_US_941_FICA_M_ADD'], 0.0 * self.FICA_M_ADD)
        self.assertPayrollEqual(rules['ER_US_941_FICA_SS'], rules['EE_US_941_FICA_SS'])
        self.assertPayrollEqual(rules['ER_US_941_FICA_M'], rules['EE_US_941_FICA_M'])
        self.assertPayrollEqual(cats['ER_US_940_FUTA'], self.FUTA_MAX_WAGE * futa_rate)

    def test_2019_taxes_with_futa_exempt(self):
        futa_rate = self.FUTA_RATE_EXEMPT / -100.0  # because of exemption

        # social security salary
        salary = self.FICA_M_ADD_START_WAGE
        employee = self._createEmployee()
        self._createContract(employee, wage=salary, fed_940_type=USHRContract.FUTA_TYPE_EXEMPT)
        self._log('2019 tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats['ER_US_940_FUTA'], 0.0)

    def test_2019_fed_income_withholding_nonresident_alien(self):
        salary = 3500.00
        schedule_pay = 'quarterly'
        w4_allowances = 1
        w4_allowance_amt = 1050.0 * w4_allowances
        nra_adjustment = 2000.0  # for quarterly
        adjusted_salary = salary - w4_allowance_amt + nra_adjustment  # 4450

        ###
        # Single QUARTERLY form Publication 15
        expected_withholding = self.float_round(-(242.50 + ((adjusted_salary - 3375) * 0.12)), self.payroll_digits)

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        schedule_pay=schedule_pay,
                                        fed_941_fit_w4_allowances=w4_allowances,
                                        fed_941_fit_w4_is_nonresident_alien=True,
                                        )

        self._log('2019 fed income single payslip nonresident alien: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()
        rules = self._getRules(payslip)
        self.assertPayrollEqual(rules['EE_US_941_FIT'], expected_withholding)

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
        contract = self._createContract(employee,
                                        wage=salary,
                                        schedule_pay=schedule_pay,
                                        fed_941_fit_w4_filing_status='married',
                                        fed_941_fit_w4_allowances=w4_allowances,
                                        fed_941_fit_w4_additional_withholding=w4_additional_withholding,
                                        )

        self._log('2019 fed income married payslip additional withholding: adjusted_salary: ' + str(adjusted_salary))
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()

        rules = self._getRules(payslip)
        self.assertPayrollEqual(rules['EE_US_941_FIT'], expected_withholding)

    def test_2019_taxes_with_w4_exempt(self):
        salary = 6000.0
        schedule_pay = 'bi-weekly'
        w4_allowances = 0
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        schedule_pay=schedule_pay,
                                        fed_941_fit_w4_allowances=w4_allowances,
                                        fed_941_fit_w4_filing_status='',
                                        )

        self._log('2019 tax w4 exempt payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        rules = self._getRules(payslip)
        self.assertPayrollEqual(rules['EE_US_941_FIT'], 0.0)

    def test_2019_taxes_with_fica_exempt(self):
        salary = 6000.0
        schedule_pay = 'bi-weekly'
        employee = self._createEmployee()
        contract = self._createContract(employee, wage=salary, schedule_pay=schedule_pay)
        contract.us_payroll_config_id.fed_941_fica_exempt = True

        self._log('2019 tax w4 exempt payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats['EE_US_941_FICA'], 0.0)
        self.assertPayrollEqual(cats['ER_US_941_FICA'], 0.0)
