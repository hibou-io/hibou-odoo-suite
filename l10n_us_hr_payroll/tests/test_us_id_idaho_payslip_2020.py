# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsIDPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    ID_UNEMP_MAX_WAGE = 41600.00
    ID_UNEMP = 1.0

    def _test_sit(self, wage, filing_status, allowances, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('ID'),
                                        id_w4_sit_filing_status=filing_status,
                                        id_w4_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('ID', self.ID_UNEMP, date(2020, 1, 1), wage_base=self.ID_UNEMP_MAX_WAGE)
        self._test_sit(1212.0, 'single', 4.0, 'bi-weekly', date(2020, 1, 1), 10.0)
        self._test_sit(10000.0, 'married', 1.0, 'annually', date(2020, 1, 1), 0.0)
        self._test_sit(52000.0, 'married', 4.0, 'monthly', date(2020, 1, 1), 3345.0)
        self._test_sit(5000.0, 'head of household', 0.0, 'semi-monthly', date(2020, 1, 1), 300.0)
        self._test_sit(5900.0, 'single', 5.0, 'weekly', date(2020, 1, 1), 367.0)
