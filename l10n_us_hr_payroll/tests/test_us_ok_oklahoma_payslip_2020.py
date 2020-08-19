# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsOKPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    OK_UNEMP_MAX_WAGE = 18700.0
    OK_UNEMP = 1.5
    # Calculation based on example https://www.ok.gov/tax/documents/2020WHTables.pdf

    def _test_sit(self, wage, filing_status, allowances, additional_withholding, exempt, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('OK'),
                                        ok_w4_sit_filing_status=filing_status,
                                        ok_w4_sit_allowances=allowances,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        state_income_tax_exempt=exempt,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('OK', self.OK_UNEMP, date(2020, 1, 1), wage_base=self.OK_UNEMP_MAX_WAGE)
        self._test_sit(1825, 'married', 2, 0, False, 'semi-monthly', date(2020, 1, 1), 46.00)
        self._test_sit(1825, 'married', 2, 0, True, 'monthly', date(2020, 1, 1), 0.00)
        self._test_sit(1000, 'single', 1, 0, False, 'weekly', date(2020, 1, 1), 39.00)
        self._test_sit(1000, 'single', 1, 10, False, 'weekly', date(2020, 1, 1), 49.00)
        self._test_sit(5000, 'head_household', 2, 10, False, 'monthly', date(2020, 1, 1), 210.00)
