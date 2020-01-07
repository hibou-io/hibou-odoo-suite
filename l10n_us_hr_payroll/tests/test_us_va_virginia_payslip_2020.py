# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date
from .common import TestUsPayslip


class TestUsVaPayslip(TestUsPayslip):
    ###
    #    Taxes and Rates
    ###
    VA_UNEMP_MAX_WAGE = 8000.0
    VA_UNEMP = 2.51
    VA_SIT_DEDUCTION = 4500.0
    VA_SIT_EXEMPTION = 930.0
    VA_SIT_OTHER_EXEMPTION = 800.0

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
                      va_va4_sit_exemptions=0,
                      va_va4_sit_other_exemptions=0,
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
                                        va_va4_sit_exemptions=va_va4_sit_exemptions,
                                        va_va4_sit_other_exemptions=va_va4_sit_other_exemptions,
                                        state_id=self.get_us_state('VA'),
                                        )
        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        # Instead of PayrollEqual after initial first round of testing.
        self.assertPayrollAlmostEqual(cats.get('EE_US_SIT', 0.0), -expected)
        return payslip

    def test_2020_taxes(self):
        self._test_er_suta('VA', self.VA_UNEMP, date(2020, 1, 1), wage_base=self.VA_UNEMP_MAX_WAGE)

        salary = 5000.0

        # For formula from https://www.tax.virginia.gov/withholding-calculator
        e1 = 2
        e2 = 0
        t = salary * 12 - (self.VA_SIT_DEDUCTION + (e1 * self.VA_SIT_EXEMPTION) + (e2 * self.VA_SIT_OTHER_EXEMPTION))

        if t <= 3000:
            w = 0.02 * t
        elif t <= 5000:
            w = 60 + (0.03 * (t - 3000))
        elif t <= 17000:
            w = 120 + (0.05 * (t - 5000))
        else:
            w = 720 + (0.0575 * (t - 17000))

        wh = w / 12

        self._run_test_sit(wage=salary,
                           schedule_pay='monthly',
                           state_income_tax_exempt=False,
                           state_income_tax_additional_withholding=0.0,
                           va_va4_sit_exemptions=e1,
                           va_va4_sit_other_exemptions=e2,
                           expected=wh,)
        self.assertPayrollEqual(wh, 235.57)  # To test against calculator

        # Below expected comes from the calculator linked above
        self._run_test_sit(wage=450.0,
                           schedule_pay='weekly',
                           state_income_tax_exempt=False,
                           state_income_tax_additional_withholding=0.0,
                           va_va4_sit_exemptions=3,
                           va_va4_sit_other_exemptions=1,
                           expected=12.22,)
        self._run_test_sit(wage=2500.0,
                           schedule_pay='bi-weekly',
                           state_income_tax_exempt=False,
                           state_income_tax_additional_withholding=0.0,
                           va_va4_sit_exemptions=1,
                           va_va4_sit_other_exemptions=0,
                           expected=121.84,)
        self._run_test_sit(wage=10000.0,
                           schedule_pay='semi-monthly',
                           state_income_tax_exempt=False,
                           state_income_tax_additional_withholding=100.0,
                           va_va4_sit_exemptions=0,
                           va_va4_sit_other_exemptions=1,
                           expected=651.57,)

        # Test exempt
        self._run_test_sit(wage=2400.0,
                           schedule_pay='monthly',
                           state_income_tax_exempt=True,
                           state_income_tax_additional_withholding=0.0,
                           va_va4_sit_exemptions=1,
                           va_va4_sit_other_exemptions=1,
                           expected=0.0,)
