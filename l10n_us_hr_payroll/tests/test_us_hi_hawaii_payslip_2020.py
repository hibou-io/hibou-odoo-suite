# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsHIPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    HI_UNEMP_MAX_WAGE = 48100.00
    HI_UNEMP = 2.4

    def _test_sit(self, wage, filing_status, additional_withholding, allowances, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('HI'),
                                        hi_hw4_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        hi_hw4_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('HI', self.HI_UNEMP, date(2020, 1, 1), wage_base=self.HI_UNEMP_MAX_WAGE)
        self._test_sit(375.0, 'single', 0.0, 3.0, 'weekly', date(2020, 1, 1), 15.3)
        self._test_sit(5000.0, 'married', 0.0, 2.0, 'monthly', date(2020, 1, 1), 287.1)
        self._test_sit(5000.0, 'married', 10.0, 2.0, 'monthly', date(2020, 1, 1), 297.1)
        self._test_sit(50000.0, 'head_of_household', 0.0, 3.0, 'weekly', date(2020, 1, 1), 3933.65)
        self._test_sit(750.0, 'single', 10.0, 3.0, 'bi-weekly', date(2020, 1, 1), 40.59)
        self._test_sit(3000.0, '', 0.0, 3.0, 'weekly', date(2020, 1, 1), 0.00)
