# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsINPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    IN_UNEMP_MAX_WAGE = 9500.0
    IN_UNEMP = 2.5
    # Calculation based on https://www.in.gov/dor/files/dn01.pdf

    def _test_sit(self, wage, additional_withholding, personal_exemption, dependent_exemption, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('IN'),
                                        state_income_tax_additional_withholding=additional_withholding,
                                        in_w4_sit_personal_exemption=personal_exemption,
                                        in_w4_sit_dependent_exemption=dependent_exemption,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('IN', self.IN_UNEMP, date(2020, 1, 1), wage_base=self.IN_UNEMP_MAX_WAGE)
        self._test_sit(800.0, 0.0, 5.0, 3.0, 'weekly', date(2020, 1, 1), 19.94)
        self._test_sit(800.0, 10.0, 5.0, 3.0, 'weekly', date(2020, 1, 1), 29.94)
        self._test_sit(9000.0, 0.0, 4.0, 3.0, 'monthly', date(2020, 1, 1), 267.82)
        self._test_sit(10000.0, 0.0, 2.0, 2.0, 'bi-weekly', date(2020, 1, 1), 316.79)
