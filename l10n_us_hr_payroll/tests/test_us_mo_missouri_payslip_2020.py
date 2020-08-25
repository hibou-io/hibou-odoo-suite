# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsMoPayslip(TestUsPayslip):
    # Calculations from http://dor.mo.gov/forms/4282_2020.pdf
    MO_UNEMP_MAX_WAGE = 11500.0
    MO_UNEMP = 2.376

    def _test_sit(self, wage, filing_status, additional_withholding, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('MO'),
                                        mo_mow4_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollAlmostEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('MO', self.MO_UNEMP, date(2020, 1, 1), wage_base=self.MO_UNEMP_MAX_WAGE)
        self._test_sit(750.0, 'single', 0.0, 'weekly', date(2020, 1, 1), 24.00)
        self._test_sit(2500.0, 'single', 5.0, 'bi-weekly', date(2020, 1, 1), 107.00)
        self._test_sit(7000.0, 'married', 0.0, 'monthly', date(2020, 1, 1), 251.00)
        self._test_sit(5000.0, 'married', 10.0, 'semi-monthly', date(2020, 1, 1), 217.00)
        self._test_sit(6000.0, '', 0.0, 'monthly', date(2020, 1, 1), 0.00)

