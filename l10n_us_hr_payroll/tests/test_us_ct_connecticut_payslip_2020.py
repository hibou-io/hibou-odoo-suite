# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsCTPayslip(TestUsPayslip):
    # Taxes and Rates
    CT_UNEMP_MAX_WAGE = 15000.0
    CT_UNEMP = 3.2

    def _test_sit(self, wage, withholding_code, additional_withholding, schedule_pay, date_start, expected_withholding):

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('CT'),
                                        ct_w4na_sit_code=withholding_code,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('CT', self.CT_UNEMP, date(2020, 1, 1), wage_base=self.CT_UNEMP_MAX_WAGE)
        self._test_sit(10000.0, 'a', 0.0, 'weekly', date(2020, 1, 1), 693.23)
        self._test_sit(12000.0, 'b', 15.0, 'bi-weekly', date(2020, 1, 1), 688.85)
        self._test_sit(5000.0, 'f', 15.0, 'monthly', date(2020, 1, 1), 230.25)
        self._test_sit(15000.0, 'c', 0.0, 'monthly', date(2020, 1, 1), 783.33)
        self._test_sit(18000.0, 'b', 0.0, 'weekly', date(2020, 1, 1), 1254.35)
        self._test_sit(500.0, 'd', 0.0, 'weekly', date(2020, 1, 1), 21.15)
