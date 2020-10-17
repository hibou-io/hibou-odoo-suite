# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip

from odoo.addons.l10n_us_hr_payroll.models.hr_contract import USHRContract

from sys import float_info


class TestUsPayslip2020(TestUsPayslip):
    # FUTA Constants
    FUTA_RATE_NORMAL = 0.6
    FUTA_RATE_BASIC = 6.0
    FUTA_RATE_EXEMPT = 0.0

    # Wage caps
    FICA_SS_MAX_WAGE = 137700.0
    FICA_M_MAX_WAGE = float_info.max
    FICA_M_ADD_START_WAGE = 200000.0
    FUTA_MAX_WAGE = 7000.0

    # Rates
    FICA_SS = 6.2 / -100.0
    FICA_M = 1.45 / -100.0
    FUTA = FUTA_RATE_NORMAL / -100.0
    FICA_M_ADD = 0.9 / -100.0

    ###
    #   2020 Taxes and Rates
    ###

    def test_2020_taxes(self):
        self.debug = False
        # salary is high so that second payslip runs over max
        # social security salary
        salary = 80000.0

        employee = self._createEmployee()

        contract = self._createContract(employee, wage=salary)
        self._log(contract.read())

        self._log('2019 tax last slip')
        payslip = self._createPayslip(employee, '2019-12-01', '2019-12-31')
        payslip.compute_sheet()
        self._log(payslip.read())
        process_payslip(payslip)

        # Ensure amounts are there, they shouldn't be added in the next year...
        cats = self._getCategories(payslip)
        self.assertTrue(cats['ER_US_940_FUTA'], self.FUTA_MAX_WAGE * self.FUTA)

        self._log('2020 tax first payslip:')
        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')
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

        self._log('2020 tax second payslip:')
        payslip = self._createPayslip(employee, '2020-02-01', '2020-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)

        self.assertPayrollEqual(rules['EE_US_941_FICA_SS'], remaining_ss_wages * self.FICA_SS)
        self.assertPayrollEqual(rules['EE_US_941_FICA_M'], remaining_m_wages * self.FICA_M)
        self.assertPayrollEqual(rules['EE_US_941_FICA_M_ADD'], 0.0)
        self.assertPayrollEqual(cats['ER_US_940_FUTA'], 0.0)

        process_payslip(payslip)

        # Make a new payslip, this one will have reached Medicare Additional (employee only)
        self._log('2020 tax third payslip:')
        payslip = self._createPayslip(employee, '2020-03-01', '2020-03-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)

        self.assertPayrollEqual(rules['EE_US_941_FICA_M_ADD'], (self.FICA_M_ADD_START_WAGE - (salary * 2)) * self.FICA_M_ADD) # aka 40k

        process_payslip(payslip)

        # Make a new payslip, this one will have all salary as Medicare Additional

        self._log('2020 tax fourth payslip:')
        payslip = self._createPayslip(employee, '2020-04-01', '2020-04-30')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)

        self.assertPayrollEqual(rules['EE_US_941_FICA_M_ADD'], salary * self.FICA_M_ADD)

        process_payslip(payslip)

    def test_2020_taxes_with_external(self):
        # social security salary
        salary = self.FICA_M_ADD_START_WAGE
        external_wages = 6000.0

        employee = self._createEmployee()

        self._createContract(employee, wage=salary, external_wages=external_wages)

        self._log('2020 tax first payslip:')
        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')
        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)
        self.assertPayrollEqual(rules['EE_US_941_FICA_SS'], (self.FICA_SS_MAX_WAGE - external_wages) * self.FICA_SS)
        self.assertPayrollEqual(rules['EE_US_941_FICA_M'], salary * self.FICA_M)
        self.assertPayrollEqual(rules['EE_US_941_FICA_M_ADD'], external_wages * self.FICA_M_ADD)
        self.assertPayrollEqual(rules['ER_US_941_FICA_SS'], rules['EE_US_941_FICA_SS'])
        self.assertPayrollEqual(rules['ER_US_941_FICA_M'], rules['EE_US_941_FICA_M'])
        self.assertPayrollEqual(cats['ER_US_940_FUTA'], (self.FUTA_MAX_WAGE - external_wages) * self.FUTA)

    def test_2020_taxes_with_full_futa(self):
        futa_rate = self.FUTA_RATE_BASIC / -100.0
        # social security salary
        salary = self.FICA_M_ADD_START_WAGE

        employee = self._createEmployee()

        self._createContract(employee, wage=salary, fed_940_type=USHRContract.FUTA_TYPE_BASIC)

        self._log('2020 tax first payslip:')
        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)
        self.assertPayrollEqual(rules['EE_US_941_FICA_SS'], self.FICA_SS_MAX_WAGE * self.FICA_SS)
        self.assertPayrollEqual(rules['EE_US_941_FICA_M'], salary * self.FICA_M)
        self.assertPayrollEqual(rules['EE_US_941_FICA_M_ADD'], 0.0 * self.FICA_M_ADD)
        self.assertPayrollEqual(rules['ER_US_941_FICA_SS'], rules['EE_US_941_FICA_SS'])
        self.assertPayrollEqual(rules['ER_US_941_FICA_M'], rules['EE_US_941_FICA_M'])
        self.assertPayrollEqual(cats['ER_US_940_FUTA'], self.FUTA_MAX_WAGE * futa_rate)

    def test_2020_taxes_with_futa_exempt(self):
        futa_rate = self.FUTA_RATE_EXEMPT / -100.0  # because of exemption

        # social security salary
        salary = self.FICA_M_ADD_START_WAGE
        employee = self._createEmployee()
        self._createContract(employee, wage=salary, fed_940_type=USHRContract.FUTA_TYPE_EXEMPT)
        self._log('2020 tax first payslip:')
        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats['ER_US_940_FUTA'], 0.0)

    def test_2020_taxes_with_fica_exempt(self):
        salary = 6000.0
        schedule_pay = 'bi-weekly'
        employee = self._createEmployee()
        contract = self._createContract(employee, wage=salary, schedule_pay=schedule_pay)
        contract.us_payroll_config_id.fed_941_fica_exempt = True

        self._log('2020 tax w4 exempt payslip:')
        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats['EE_US_941_FICA'], 0.0)
        self.assertPayrollEqual(cats['ER_US_941_FICA'], 0.0)

    """
    For Federal Income Tax Withholding, we are utilizing the calculations from the new IRS Excel calculator.
    Given that you CAN round, we will round to compare even though we will calculate as close to the penny as possible
    with the wage * computed_percent method.
    """

    def _run_test_fit(self,
                      wage=0.0,
                      schedule_pay='monthly',
                      filing_status='single',
                      dependent_credit=0.0,
                      other_income=0.0,
                      deductions=0.0,
                      additional_withholding=0.0,
                      is_nonresident_alien=False,
                      expected_standard=0.0,
                      expected_higher=0.0,
                      ):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        schedule_pay=schedule_pay,
                                        fed_941_fit_w4_is_nonresident_alien=is_nonresident_alien,
                                        fed_941_fit_w4_filing_status=filing_status,
                                        fed_941_fit_w4_multiple_jobs_higher=False,
                                        fed_941_fit_w4_dependent_credit=dependent_credit,
                                        fed_941_fit_w4_other_income=other_income,
                                        fed_941_fit_w4_deductions=deductions,
                                        fed_941_fit_w4_additional_withholding=additional_withholding,
                                        )
        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertPayrollEqual(round(cats.get('EE_US_941_FIT', 0.0)), -expected_standard)

        contract.us_payroll_config_id.fed_941_fit_w4_multiple_jobs_higher = True
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertPayrollEqual(round(cats.get('EE_US_941_FIT', 0.0)), -expected_higher)
        return payslip

    def test_2020_fed_income_withholding_single(self):
        _ = self._run_test_fit(
            wage=6000.0,
            schedule_pay='monthly',
            filing_status='single',
            dependent_credit=100.0,
            other_income=200.0,
            deductions=300.0,
            additional_withholding=400.0,
            is_nonresident_alien=False,
            expected_standard=1132.0,
            expected_higher=1459.0,
        )

    def test_2020_fed_income_withholding_married_as_single(self):
        # This is "Head of Household" though the field name is the same for historical reasons.
        _ = self._run_test_fit(
            wage=500.0,
            schedule_pay='weekly',
            filing_status='married_as_single',
            dependent_credit=20.0,
            other_income=30.0,
            deductions=40.0,
            additional_withholding=10.0,
            is_nonresident_alien=False,
            expected_standard=24.0,
            expected_higher=45.0,
        )

    def test_2020_fed_income_withholding_married(self):
        _ = self._run_test_fit(
            wage=14000.00,
            schedule_pay='bi-weekly',
            filing_status='married',
            dependent_credit=2500.0,
            other_income=1200.0,
            deductions=1000.0,
            additional_withholding=0.0,
            is_nonresident_alien=False,
            expected_standard=2621.0,
            expected_higher=3702.0,
        )

    def test_2020_fed_income_withholding_nonresident_alien(self):
        # Monthly NRA additional wage is 1033.30
        # Wage input on IRS Form entered as (3500+1033.30)=4533.30, not 3500.0
        _ = self._run_test_fit(
            wage=3500.00,
            schedule_pay='monthly',
            filing_status='married',
            dependent_credit=340.0,
            other_income=0.0,
            deductions=0.0,
            additional_withholding=0.0,
            is_nonresident_alien=True,
            expected_standard=235.0,
            expected_higher=391.0,
        )

    def test_2020_taxes_with_w4_exempt(self):
        _ = self._run_test_fit(
            wage=3500.00,
            schedule_pay='monthly',
            filing_status='',  # Exempt
            dependent_credit=340.0,
            other_income=0.0,
            deductions=0.0,
            additional_withholding=0.0,
            is_nonresident_alien=True,
            expected_standard=0.0,
            expected_higher=0.0,
        )
