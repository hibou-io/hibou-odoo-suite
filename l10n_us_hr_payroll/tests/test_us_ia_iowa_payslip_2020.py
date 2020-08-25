# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsIAPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    IA_UNEMP_MAX_WAGE = 31600.00
    IA_UNEMP = 1.0

    def _test_sit(self, wage, exempt, additional_withholding, allowances, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('IA'),
                                        state_income_tax_exempt=exempt,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        ia_w4_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollAlmostEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('IA', self.IA_UNEMP, date(2020, 1, 1), wage_base=self.IA_UNEMP_MAX_WAGE)
        self._test_sit(2100.0, False, 0.0, 3.0, 'bi-weekly', date(2020, 1, 1), 83.5)
        self._test_sit(3000.0, True, 10.0, 1.0, 'bi-weekly', date(2020, 1, 1), 0.00)
        self._test_sit(300.0, False, 0.0, 1.0, 'weekly', date(2020, 1, 1), 6.77)
        self._test_sit(5000.0, False, 0.0, 1.0, 'monthly', date(2020, 1, 1), 230.76)
        self._test_sit(7500.0, False, 10.0, 2.0, 'semi-monthly', date(2020, 1, 1), 432.84)
