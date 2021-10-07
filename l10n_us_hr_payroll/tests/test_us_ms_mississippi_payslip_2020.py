# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsMsPayslip(TestUsPayslip):
    # Calculations from https://www.dor.ms.gov/Documents/Computer%20Payroll%20Flowchart.pdf
    MS_UNEMP = 1.2
    MS_UNEMP_MAX_WAGE = 14000.0

    def _test_sit(self, wage, filing_status, additional_withholding, exemption, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('MS'),
                                        ms_89_350_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        ms_89_350_sit_exemption_value=exemption,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollAlmostEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('MS', self.MS_UNEMP, date(2020, 1, 1), wage_base=self.MS_UNEMP_MAX_WAGE)
        self._test_sit(1250.0, 'head_of_household', 0.0, 11000, 'semi-monthly', date(2020, 1, 1), 22.00)
        self._test_sit(500.0, '', 5.0, 0, 'bi-weekly', date(2020, 1, 1), 0.00)
        self._test_sit(12000.0, 'single', 0.0, 11000, 'monthly', date(2020, 1, 1), 525.00)
        self._test_sit(2500.0, 'married', 5.0, 500, 'bi-weekly', date(2020, 1, 1), 111.00)


