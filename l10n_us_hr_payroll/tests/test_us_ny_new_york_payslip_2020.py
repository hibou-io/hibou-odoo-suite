# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsNYPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    NY_UNEMP_MAX_WAGE = 11600.0
    NY_UNEMP = 2.5
    NY_RSF = 0.075
    NY_MCTMT = 0.0

    def _test_sit(self, wage, filing_status, additional_withholding,  allowances,  schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('NY'),
                                        ny_it2104_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        ny_it2104_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollAlmostEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        combined_er_rate = self.NY_UNEMP + self.NY_RSF + self.NY_MCTMT
        self._test_er_suta('NY', combined_er_rate, date(2020, 1, 1), wage_base=self.NY_UNEMP_MAX_WAGE, relaxed=True)
        self._test_sit(400.0, 'single', 0.0, 3, 'weekly', date(2020, 1, 1), 8.20)
        self._test_sit(10000.0, 'single', 0.0, 3, 'monthly', date(2020, 1, 1), 554.09)
        self._test_sit(8000.0, 'married', 0.0, 5, 'monthly', date(2020, 1, 1), 400.32)
        self._test_sit(4500.0, 'married', 10.0, 3, 'semi-monthly', date(2020, 1, 1), 247.69)
        self._test_sit(50000.0, '', 0.0, 0, 'monthly', date(2020, 1, 1), 0.00)
