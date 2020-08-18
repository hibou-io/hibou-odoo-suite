# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsNDPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    ND_UNEMP_MAX_WAGE = 37900.0
    ND_UNEMP = 1.02
    # Calculation based on this file page.47 https://www.nd.gov/tax/data/upfiles/media/rates-and-instructions.pdf?20200110115917

    def _test_sit(self, wage, filing_status,  additional_withholding, allowances, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('ND'),
                                        nd_w4_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        nd_w4_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollAlmostEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('ND', self.ND_UNEMP, date(2020, 1, 1), wage_base=self.ND_UNEMP_MAX_WAGE)
        self._test_sit(700.0, 'single', 0.0, 0.0, 'weekly', date(2020, 1, 1), 6.0)
        self._test_sit(5000.0, 'married', 0.0, 2.0, 'bi-weekly', date(2020, 1, 1), 76.0)
        self._test_sit(25000.0, 'head_household', 0.0, 0.0, 'monthly', date(2020, 1, 1), 534.0)
        self._test_sit(25000.0, 'head_household', 10.0, 2.0, 'monthly', date(2020, 1, 1), 525.0)
        self._test_sit(3000.0, '', 10.0, 2.0, 'monthly', date(2020, 1, 1), 0.0)
