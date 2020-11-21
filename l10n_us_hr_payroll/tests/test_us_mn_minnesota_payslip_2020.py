# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsMNPayslip(TestUsPayslip):
    # TAXES AND RATES
    MN_UNEMP_MAX_WAGE = 35000.0
    MN_UNEMP = 1.11

    def _test_sit(self, wage, filing_status, allowances, additional_withholding, schedule_pay, date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('MN'),
                                        mn_w4mn_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        mn_w4mn_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)

        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('MN', self.MN_UNEMP, date(2020, 1, 1), wage_base=self.MN_UNEMP_MAX_WAGE)
        self._test_sit(5000.0, 'single', 1.0, 0.0, 'weekly', date(2020, 1, 1), 389.0)
        self._test_sit(30000.0, 'single', 1.0, 0.0, 'weekly', date(2020, 1, 1), 2850.99)
        self._test_sit(5000.0, 'married', 1.0, 0.0, 'weekly', date(2020, 1, 1), 325.0)
        self._test_sit(6500.0, 'single', 1.0, 0.0, 'semi-monthly', date(2020, 1, 1), 429.0)
        self._test_sit(5500.0, '', 2.0, 0.0, 'weekly', date(2020, 1, 1), 0.0)
        self._test_sit(5500.0, 'single', 2.0, 40.0, 'weekly', date(2020, 1, 1), 470.0)
