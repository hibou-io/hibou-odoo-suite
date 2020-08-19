# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsVTPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    VT_UNEMP_MAX_WAGE = 16100.0
    VT_UNEMP = 1.0
    # Calculation based on example https://tax.vermont.gov/sites/tax/files/documents/WithholdingInstructions.pdf

    def _test_sit(self, wage, filing_status, allowances, additional_withholding, exempt, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('VT'),
                                        vt_w4vt_sit_filing_status=filing_status,
                                        vt_w4vt_sit_allowances=allowances,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        state_income_tax_exempt=exempt,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('VT', self.VT_UNEMP, date(2020, 1, 1), wage_base=self.VT_UNEMP_MAX_WAGE)
        self._test_sit(1800, 'married', 2, 0, False, 'weekly', date(2020, 1, 1), 53.73)
        self._test_sit(1800, 'married', 2, 10, False, 'weekly', date(2020, 1, 1), 63.73)
        self._test_sit(1000, 'single', 1, 0, True, 'weekly', date(2020, 1, 1), 0.00)
        self._test_sit(8000, 'single', 1, 10, False, 'bi-weekly', date(2020, 1, 1), 506.58)
