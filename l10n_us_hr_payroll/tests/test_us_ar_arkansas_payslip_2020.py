# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsARPayslip(TestUsPayslip):
    # Taxes and Rates
    AR_UNEMP_MAX_WAGE = 8000.0
    AR_UNEMP = 2.9

    def _test_sit(self, wage, exemptions, allowances, additional_withholding, schedule_pay, date_start, expected_withholding):

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('AR'),
                                        state_income_tax_exempt=exemptions,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        ar_ar4ec_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('AR', self.AR_UNEMP, date(2020, 1, 1), wage_base=self.AR_UNEMP_MAX_WAGE)
        self._test_sit(5000.0, True, 0.0, 0, 'monthly', date(2020, 1, 1), 0.0)
        self._test_sit(5000.0, False, 0.0, 0, 'monthly', date(2020, 1, 1), 221.0)
        self._test_sit(700.0, False, 0.0, 150, 'weekly', date(2020, 1, 1), 175.0)
        self._test_sit(7000.0, False, 2.0, 0, 'semi-monthly', date(2020, 1, 1), 420.0)
        self._test_sit(3000.0, False, 1.0, 0, 'bi-weekly', date(2020, 1, 1), 142.0)
