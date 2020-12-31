# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsILPayslip(TestUsPayslip):
    # Taxes and Rates
    IL_UNEMP_MAX_WAGE = 12960.0
    IL_UNEMP = 3.175

    def _test_sit(self, wage, additional_withholding, basic_allowances, additional_allowances, schedule_pay, date_start, expected_withholding):

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('IL'),
                                        state_income_tax_additional_withholding=additional_withholding,
                                        il_w4_sit_basic_allowances=basic_allowances,
                                        il_w4_sit_additional_allowances=additional_allowances,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2021_taxes_example(self):
        self._test_er_suta('IL', self.IL_UNEMP, date(2021, 1, 1), wage_base=self.IL_UNEMP_MAX_WAGE, relaxed=True)
        self._test_sit(800.0, 0.0, 2, 2, 'weekly', date(2021, 1, 1), 33.17)
        self._test_sit(800.0, 10.0, 2, 2, 'weekly', date(2021, 1, 1), 43.17)
        self._test_sit(2500.0, 0.0, 1, 1, 'monthly', date(2021, 1, 1), 109.83)
        self._test_sit(2500.0, 0.0, 0, 0, 'monthly', date(2021, 1, 1), 123.75)
        self._test_sit(3000.0, 15.0, 0, 0, 'quarterly', date(2021, 1, 1), 163.50)

