# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsGAPayslip(TestUsPayslip):

    # TAXES AND RATES
    GA_UNEMP_MAX_WAGE = 9500.00
    GA_UNEMP = 2.70

    # Example calculated based on https://dor.georgia.gov/employers-tax-guide 2020_employer tax gauide

    def _test_sit(self, wage, filing_status, additional_withholding, dependent_allowances, additional_allowances,
                  schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('GA'),
                                        ga_g4_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        ga_g4_sit_dependent_allowances=dependent_allowances,
                                        ga_g4_sit_additional_allowances=additional_allowances,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollAlmostEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('GA', self.GA_UNEMP, date(2020, 1, 1), wage_base=self.GA_UNEMP_MAX_WAGE)
        self._test_sit(15000.0, 'single', 12.50, 1, 0, 'weekly', date(2020, 1, 1), 860.28)
        self._test_sit(25000.0, 'head of household', 15.00, 2, 0, 'monthly', date(2020, 1, 1), 1369.19)
        self._test_sit(425.0, 'married filing separate', 0.0, 1, 0, 'weekly', date(2020, 1, 1), 11.45)
        self._test_sit(3000.0, 'single', 0.00, 1, 1, 'quarterly', date(2020, 1, 1), 0.0)
        self._test_sit(2500.0, '', 0.00, 1, 1, 'quarterly', date(2020, 1, 1), 0.0)
