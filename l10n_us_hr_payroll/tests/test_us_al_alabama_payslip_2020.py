# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsALPayslip(TestUsPayslip):
    # Taxes and Rates
    AL_UNEMP_MAX_WAGE = 8000.00
    AL_UNEMP = 2.70

    def _test_sit(self, wage, exempt, exemptions, additional_withholding, dependent, schedule_pay, date_start, expected_withholding):

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('AL'),
                                        al_a4_sit_exemptions=exempt,
                                        state_income_tax_exempt=exemptions,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        al_a4_sit_dependents=dependent,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('AL', self.AL_UNEMP, date(2020, 1, 1), wage_base=self.AL_UNEMP_MAX_WAGE)
        self._test_sit(10000.0, 'S', False, 0.0, 1.0, 'weekly', date(2020, 1, 1), 349.08)
        self._test_sit(850.0, 'M', False, 0.0, 2.0, 'weekly', date(2020, 1, 1), 29.98)
        self._test_sit(5000.0, 'H', False, 0.0, 2.0, 'bi-weekly', date(2020, 1, 1), 191.15)
        self._test_sit(20000.0, 'MS', False, 2.0, 0, 'monthly', date(2020, 1, 1), 757.6)
        self._test_sit(5500.0, '', True, 2.0, 150, 'weekly', date(2020, 1, 1), 0.00)
