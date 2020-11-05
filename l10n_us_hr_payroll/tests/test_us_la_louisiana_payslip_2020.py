# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsLAPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    LA_UNEMP_MAX_WAGE = 7700.0
    LA_UNEMP = 1.14
    # Calculation based on http://revenue.louisiana.gov/TaxForms/1306(1_12)TF.pdf

    def _test_sit(self, wage, filing_status, additional_withholding, exemptions, dependents, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('LA'),
                                        la_l4_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        la_l4_sit_exemptions=exemptions,
                                        la_l4_sit_dependents=dependents,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollAlmostEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('LA', self.LA_UNEMP, date(2020, 1, 1), wage_base=self.LA_UNEMP_MAX_WAGE)
        self._test_sit(700.0, 'single', 0.0, 1.0, 2.0, 'weekly', date(2020, 1, 1), 19.43)
        self._test_sit(4600.0, 'married', 0.0, 2.0, 3.0, 'bi-weekly', date(2020, 1, 1), 157.12)
        self._test_sit(6000.0, 'single', 10.0, 2.0, 3.0, 'monthly', date(2020, 1, 1), 219.08)
