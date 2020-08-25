# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsMEPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    ME_UNEMP_MAX_WAGE = 12000.0
    ME_UNEMP = 1.92
    # Calculation based on this file page.6 and 7 https://www.maine.gov/revenue/forms/with/2020/20_WH_Tab&Instructions.pdf

    def _test_sit(self, wage, filing_status, additional_withholding, exempt, allowances, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('ME'),
                                        me_w4me_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        state_income_tax_exempt=exempt,
                                        me_w4me_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollAlmostEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('ME', self.ME_UNEMP, date(2020, 1, 1), wage_base=self.ME_UNEMP_MAX_WAGE)
        self._test_sit(300.0, 'single', 0.0, False, 2, 'weekly', date(2020, 1, 1), 0.0)
        self._test_sit(800.0, 'single', 0.0, False, 2, 'bi-weekly', date(2020, 1, 1), 6.00)
        self._test_sit(4500.0, 'married', 0.0, True, 0, 'weekly', date(2020, 1, 1), 0.00)
        self._test_sit(4500.0, 'married', 0.0, False, 2, 'monthly', date(2020, 1, 1), 113.00)
        self._test_sit(4500.0, 'married', 10.0, False, 2, 'weekly', date(2020, 1, 1), 287.00)
        self._test_sit(7000.0, '', 10.0, False, 2, 'weekly', date(2020, 1, 1), 0.00)
