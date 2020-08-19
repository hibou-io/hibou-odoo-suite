# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsKSPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    KS_UNEMP_MAX_WAGE = 14000.0
    KS_UNEMP = 2.7
    # Calculation based on example https://revenue.ky.gov/Forms/42A003(T)%20(12-2019)%202020%20Tax%20Tables.pdf

    def _test_sit(self, wage, filing_status, allowances, additional_withholding, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('KS'),
                                        ks_k4_sit_filing_status=filing_status,
                                        ks_k4_sit_allowances=allowances,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollAlmostEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('KS', self.KS_UNEMP, date(2020, 1, 1), wage_base=self.KS_UNEMP_MAX_WAGE)
        self._test_sit(6250, 'married', 2, 0, 'semi-monthly', date(2020, 1, 1), 290.00)
        self._test_sit(5000, 'single', 1, 0, 'monthly', date(2020, 1, 1), 222.00)
        self._test_sit(1500, 'married', 0, 0,  'bi-weekly', date(2020, 1, 1), 39.00)
        self._test_sit(750, 'single', 2, 10,  'weekly', date(2020, 1, 1), 36.00)
