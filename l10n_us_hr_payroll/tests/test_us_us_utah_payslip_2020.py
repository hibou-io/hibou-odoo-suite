# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsUTPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    UT_UNEMP_MAX_WAGE = 36600.0
    UT_UNEMP = 0.1
    # Calculation based on example https://tax.utah.gov/forms/pubs/pub-14.pdf

    def _test_sit(self, wage, filing_status, additional_withholding, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('UT'),
                                        ut_w4_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollAlmostEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('UT', self.UT_UNEMP, date(2020, 1, 1), wage_base=self.UT_UNEMP_MAX_WAGE)
        self._test_sit(400, 'single', 0, 'weekly', date(2020, 1, 1), 16.00)
        self._test_sit(1000, 'single', 0, 'bi-weekly', date(2020, 1, 1), 45.00)
        self._test_sit(855, 'married', 0, 'semi-monthly', date(2020, 1, 1), 16.00)
        self._test_sit(2500, 'married', 0, 'monthly', date(2020, 1, 1), 81.00)
        self._test_sit(8000, 'head_household', 10, 'quarterly', date(2020, 1, 1), 397.00)
