# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsWVPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    WV_UNEMP_MAX_WAGE = 12000.0
    WV_UNEMP = 2.7
    # Calculation based on example https://tax.wv.gov/Documents/TaxForms/it100.1a.pdf

    def _test_sit(self, wage, filing_status, exemption, additional_withholding, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('WV'),
                                        wv_it104_sit_filing_status=filing_status,
                                        wv_it104_sit_exemptions=exemption,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('WV', self.WV_UNEMP, date(2020, 1, 1), wage_base=self.WV_UNEMP_MAX_WAGE)
        self._test_sit(1250, 'married', 2, 0, 'semi-monthly', date(2020, 1, 1), 44.00)
        self._test_sit(1300, 'single', 1, 0, 'bi-weekly', date(2020, 1, 1), 46.00)
        self._test_sit(1300, 'single', 1, 10, 'bi-weekly', date(2020, 1, 1), 56.00)
        self._test_sit(15000, 'single', 2, 0, 'monthly', date(2020, 1, 1), 860.00)
