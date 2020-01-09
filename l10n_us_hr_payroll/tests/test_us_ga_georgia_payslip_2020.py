# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date
from .common import TestUsPayslip, process_payslip


class TestUsGAPayslip(TestUsPayslip):

    # TAXES AND RATES
    GA_UNEMP_MAX_WAGE = 9500.00
    GA_UNEMP = 2.70

    def _run_test_sit(self,
                      wage=0.0,
                      schedule_pay='monthly',
                      filing_status='single',
                      dependent_credit=0.0,
                      other_income=0.0,
                      deductions=0.0,
                      additional_withholding=0.0,
                      is_nonresident_alien=False,
                      state_income_tax_exempt=False,
                      state_income_tax_additional_withholding=0.0,
                      ga_g4_sit_dependent_allowances=0,
                      ga_g4_sit_additional_allowances=0,
                      ga_g4_sit_filing_status=None,
                      expected=0.0,
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
                                        state_income_tax_exempt=state_income_tax_exempt,
                                        state_income_tax_additional_withholding=state_income_tax_additional_withholding,
                                        ga_g4_sit_dependent_allowances=ga_g4_sit_dependent_allowances,
                                        ga_g4_sit_additional_allowances=ga_g4_sit_additional_allowances,
                                        ga_g4_sit_filing_status=ga_g4_sit_filing_status,
                                        state_id=self.get_us_state('GA'),
                                        )
        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        # Instead of PayrollEqual after initial first round of testing.
        self.assertPayrollAlmostEqual(cats.get('EE_US_SIT', 0.0), -expected)
        return payslip

    def test_taxes_weekly_single_with_additional_wh(self):
        self._test_er_suta('GA', self.GA_UNEMP, date(2020, 1, 1), wage_base=self.GA_UNEMP_MAX_WAGE)
        salary = 15000.00
        schedule_pay = 'weekly'
        allowances = 1
        filing_status = 'single'
        additional_wh = 12.50
        # Hand Calculated Amount to Test
        # Step 1 - Subtract standard deduction from wages. Std Deduct for single weekly is 88.50
        # step1 = 15000.00 - 88.50 = 14911.5
        # Step 2 - Subtract personal allowance from step1. Allowance for single weekly is 51.92
        # step2 = step1 - 51.92 = 14859.58
        # Step 3 - Subtract amount for dependents. Weekly dependent allowance is 57.50
        # step3 = 14859.58 - 57.50 = 14802.08
        # Step 4 -Determine wh amount from tables
        # step4 = 4.42 + ((5.75 / 100.00) * (14802.08 - 135.00))
        # Add additional_wh
        # wh = 847.7771 + 12.50 = 860.2771
        wh = 860.28

        self._run_test_sit(wage=salary,
                           schedule_pay=schedule_pay,
                           state_income_tax_additional_withholding=additional_wh,
                           ga_g4_sit_dependent_allowances=allowances,
                           ga_g4_sit_additional_allowances=0,
                           ga_g4_sit_filing_status=filing_status,
                           expected=wh,
                           )


    def test_taxes_monthly_head_of_household(self):
        salary = 25000.00
        schedule_pay = 'monthly'
        allowances = 2
        filing_status = 'head of household'
        additional_wh = 15.00
        # Hand Calculated Amount to Test
        # Step 1 - Subtract standard deduction from wages. Std Deduct for head of household monthly is 383.50
        # step1 = 25000.00 - 383.50 = 24616.5
        # Step 2 - Subtract personal allowance from step1. Allowance for head of household monthly is 225.00
        # step2 = 24616.5 - 225.00 = 24391.5
        # Step 3 - Subtract amount for dependents. Weekly dependent allowance is 250.00
        # step3 = 24391.5 - (2 * 250.00) = 23891.5
        # Step 4 - Determine wh amount from tables
        # step4 = 28.33 + ((5.75 / 100.00) * (23891.5 - 833.00)) = 1354.19375
        # Add additional_wh
        # wh = 1354.19375 + 15.00 = 1369.19375
        wh = 1369.19

        self._run_test_sit(wage=salary,
                           schedule_pay=schedule_pay,
                           state_income_tax_additional_withholding=additional_wh,
                           ga_g4_sit_dependent_allowances=allowances,
                           ga_g4_sit_additional_allowances=0,
                           ga_g4_sit_filing_status=filing_status,
                           expected=wh,
                           )

        # additional from external calculator
        self._run_test_sit(wage=425.0,
                           schedule_pay='weekly',
                           state_income_tax_additional_withholding=0.0,
                           ga_g4_sit_dependent_allowances=1,
                           ga_g4_sit_additional_allowances=0,
                           ga_g4_sit_filing_status='married filing separate',
                           expected=11.45,
                           )

        self._run_test_sit(wage=3000.0,
                           schedule_pay='quarterly',
                           state_income_tax_additional_withholding=0.0,
                           ga_g4_sit_dependent_allowances=1,
                           ga_g4_sit_additional_allowances=1,
                           ga_g4_sit_filing_status='single',
                           expected=0.0,
                           )

        # TODO 'married filing joint, both spouses working' returns lower than calculator
        # TODO 'married filing joint, one spouse working' returns lower than calculator

    def test_taxes_exempt(self):
        salary = 25000.00
        schedule_pay = 'monthly'
        allowances = 2
        filing_status = 'exempt'
        additional_wh = 15.00

        self._run_test_sit(wage=salary,
                           schedule_pay=schedule_pay,
                           state_income_tax_additional_withholding=additional_wh,
                           ga_g4_sit_dependent_allowances=allowances,
                           ga_g4_sit_additional_allowances=0,
                           ga_g4_sit_filing_status=filing_status,
                           expected=0.0,
                           )
