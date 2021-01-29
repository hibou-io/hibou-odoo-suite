# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsKYPayslip(TestUsPayslip):
    ###
    #   2021 Taxes and Rates
    ###
    KY_UNEMP_MAX_WAGE = 11100.0
    KY_UNEMP = 2.7
    # Calculation based on example https://revenue.ky.gov/Forms/42A003(T)%20(12-2019)%202120%20Tax%20Tables.pdf

    def _test_sit(self, wage, additional_withholding, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('KY'),
                                        state_income_tax_additional_withholding=additional_withholding,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2021_taxes_example(self):
        self._test_er_suta('KY', self.KY_UNEMP, date(2021, 1, 1), wage_base=self.KY_UNEMP_MAX_WAGE)
        # page 8 of https://revenue.ky.gov/Software-Developer/Software%20Development%20Documents/2021%20Withholding%20Tax%20Tables%20-%20Computer%20Formual%2042A003(T)(12-20)(10-15-20%20DRAFT).pdf
        self._test_sit(3020, 0.0, 'monthly', date(2021, 1, 1), 139.79)
        self._test_sit(1500, 0.0, 'bi-weekly', date(2021, 1, 1), 69.83)
        self._test_sit(1500, 10.0, 'bi-weekly', date(2021, 1, 1), 79.83)
        self._test_sit(750, 00.0, 'weekly', date(2021, 1, 1), 34.91)
        self._test_sit(7000, 0.0, 'semi-monthly', date(2021, 1, 1), 344.39)
