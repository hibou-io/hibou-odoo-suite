# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date
from .common import TestUsPayslip, process_payslip


class TestUsOhPayslip(TestUsPayslip):
    ###
    #    Taxes and Rates
    ###
    OH_UNEMP_MAX_WAGE = 9000.0
    OH_UNEMP = 2.7

    def test_2020_taxes(self):
        self._test_er_suta('OH', self.OH_UNEMP, date(2020, 1, 1), wage_base=self.OH_UNEMP_MAX_WAGE)

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
                      oh_it4_sit_exemptions=0,
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
                                        oh_it4_sit_exemptions=oh_it4_sit_exemptions,
                                        state_id=self.get_us_state('OH'),
                                        )
        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        # Instead of PayrollEqual after initial first round of testing.
        self.assertPayrollAlmostEqual(cats.get('EE_US_SIT', 0.0), -expected)
        return payslip

    def test_2020_sit_1(self):
        wage = 400.0
        exemptions = 1
        additional = 10.0
        pay_periods = 12.0
        annual_adjusted_wage = (wage * pay_periods) - (650.0 * exemptions)
        self.assertPayrollEqual(4150.0, annual_adjusted_wage)
        WD = ((annual_adjusted_wage * 0.005) / pay_periods) * 1.032
        self.assertPayrollEqual(WD, 1.7845)
        expected = WD + additional
        self._run_test_sit(wage=wage,
                           schedule_pay='monthly',
                           state_income_tax_exempt=False,
                           state_income_tax_additional_withholding=additional,
                           oh_it4_sit_exemptions=exemptions,
                           expected=expected,
                           )

        # the above agrees with online calculator to the penny 0.01
        # below expected coming from calculator to 0.10
        #
        # semi-monthly
        self._run_test_sit(wage=1200,
                           schedule_pay='semi-monthly',
                           state_income_tax_exempt=False,
                           state_income_tax_additional_withholding=20.0,
                           oh_it4_sit_exemptions=2,
                           expected=42.58,
                           )

        # bi-weekly
        self._run_test_sit(wage=3000,
                           schedule_pay='bi-weekly',
                           state_income_tax_exempt=False,
                           #state_income_tax_additional_withholding=0.0,
                           oh_it4_sit_exemptions=0,
                           expected=88.51,
                           )
        # weekly
        self._run_test_sit(wage=355,
                           schedule_pay='weekly',
                           state_income_tax_exempt=False,
                           # state_income_tax_additional_withholding=0.0,
                           oh_it4_sit_exemptions=1,
                           expected=4.87,
                           )

        # Exempt!
        self._run_test_sit(wage=355,
                           schedule_pay='weekly',
                           state_income_tax_exempt=True,
                           # state_income_tax_additional_withholding=0.0,
                           oh_it4_sit_exemptions=1,
                           expected=0.0,
                           )
