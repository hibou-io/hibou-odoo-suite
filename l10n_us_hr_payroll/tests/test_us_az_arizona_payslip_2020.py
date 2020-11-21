# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsAZPayslip(TestUsPayslip):
    # Taxes and Rates
    AZ_UNEMP_MAX_WAGE = 7000.0
    AZ_UNEMP = 2.0

    def _test_sit(self, wage, additional_withholding, withholding_percent, schedule_pay, date_start, expected_withholding):

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('AZ'),
                                        state_income_tax_additional_withholding=additional_withholding,
                                        az_a4_sit_withholding_percentage=withholding_percent,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('AZ', self.AZ_UNEMP, date(2020, 1, 1), wage_base=self.AZ_UNEMP_MAX_WAGE)
        self._test_sit(1000.0, 0.0, 2.70, 'monthly', date(2020, 1, 1), 27.0)
        self._test_sit(1000.0, 10.0, 2.70, 'monthly', date(2020, 1, 1), 37.0)
        self._test_sit(15000.0, 0.0, 3.60, 'weekly', date(2020, 1, 1), 540.0)
        self._test_sit(8000.0, 0.0, 4.20, 'semi-monthly', date(2020, 1, 1), 336.0)
        self._test_sit(8000.0, 0.0, 0.00, 'semi-monthly', date(2020, 1, 1), 0.0)
