# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsMIPayslip(TestUsPayslip):
    # Taxes and Rates
    MI_UNEMP_MAX_WAGE = 9000.0
    MI_UNEMP = 2.7

    def _test_sit(self, wage, exemptions, additional_withholding, schedule_pay, date_start, expected_withholding):

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('MI'),
                                        mi_w4_sit_exemptions=exemptions,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('MI', self.MI_UNEMP, date(2020, 1, 1), wage_base=self.MI_UNEMP_MAX_WAGE)
        self._test_sit(750.0, 1, 100.0, 'weekly', date(2020, 1, 1), 127.99)
        self._test_sit(1750.0, 1, 0.0, 'bi-weekly', date(2020, 1, 1), 66.61)
        self._test_sit(5000.0, 1, 5.0, 'semi-monthly', date(2020, 1, 1), 209.09)
        self._test_sit(8000.0, 1, 5.0, 'monthly', date(2020, 1, 1), 328.18)
        self._test_sit(5000.0, 2, 0.0, 'monthly', date(2020, 1, 1), 178.86)

