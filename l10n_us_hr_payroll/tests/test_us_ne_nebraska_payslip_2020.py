# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsNEPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    NE_UNEMP_MAX_WAGE = 9000.0
    NE_UNEMP = 1.25

    def _test_sit(self, wage, filing_status,  exempt,  additional_withholding, allowances, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('NE'),
                                        ne_w4n_sit_filing_status=filing_status,
                                        state_income_tax_exempt=exempt,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        ne_w4n_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollAlmostEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('NE', self.NE_UNEMP, date(2020, 1, 1), wage_base=self.NE_UNEMP_MAX_WAGE)
        self._test_sit(750.0, 'single', False, 0.0, 2, 'weekly', date(2020, 1, 1), 27.53)
        self._test_sit(9500.0, 'single', False, 0.0, 1, 'bi-weekly', date(2020, 1, 1), 612.63)
        self._test_sit(10500.0, 'married', False, 0.0, 1, 'bi-weekly', date(2020, 1, 1), 659.85)
        self._test_sit(9500.0, 'single', True, 0.0, 1, 'bi-weekly', date(2020, 1, 1), 0.0)
        self._test_sit(10500.0, 'single', False, 10.0, 2, 'monthly', date(2020, 1, 1), 625.2)
        self._test_sit(4000.0, 'single', False, 0.0, 1, 'monthly', date(2020, 1, 1), 179.44)
