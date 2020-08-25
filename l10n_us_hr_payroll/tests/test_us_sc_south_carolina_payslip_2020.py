# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsSCPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    SC_UNEMP_MAX_WAGE = 14000.0
    SC_UNEMP = 0.55
    # Calculation based on https://dor.sc.gov/forms-site/Forms/WH1603F_2020.pdf

    def _test_sit(self, wage, additional_withholding, exempt, allowances,  schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('SC'),
                                        state_income_tax_additional_withholding=additional_withholding,
                                        state_income_tax_exempt=exempt,
                                        sc_w4_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollAlmostEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('SC', self.SC_UNEMP, date(2020, 1, 1), wage_base=self.SC_UNEMP_MAX_WAGE)
        self._test_sit(750.0, 0.0, False, 3.0, 'weekly', date(2020, 1, 1), 28.73)
        self._test_sit(800.0, 0.0, True, 0.0, 'weekly', date(2020, 1, 1), 0.00)
        self._test_sit(9000.0, 0.0, False, 0.0, 'monthly', date(2020, 1, 1), 594.61)
        self._test_sit(5000.0, 10.0, False, 2.0, 'semi-monthly', date(2020, 1, 1), 316.06)
