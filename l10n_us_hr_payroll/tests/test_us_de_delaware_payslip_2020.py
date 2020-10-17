# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsDEPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    DE_UNEMP_MAX_WAGE = 16500.0
    DE_UNEMP = 1.50
    # Calculation based on section 17. https://revenue.delaware.gov/employers-guide-withholding-regulations-employers-duties/

    def _test_sit(self, wage, filing_status, additional_withholding, dependents, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('DE'),
                                        de_w4_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        de_w4_sit_dependent=dependents,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('DE', self.DE_UNEMP, date(2020, 1, 1), wage_base=self.DE_UNEMP_MAX_WAGE)
        self._test_sit(480.77, 'single', 0.0, 1.0, 'weekly', date(2020, 1, 1), 13.88)
        self._test_sit(5000.0, 'single', 0.0, 2.0, 'monthly', date(2020, 1, 1), 211.93)
        self._test_sit(5000.0, 'single', 10.0, 1.0, 'monthly', date(2020, 1, 1), 231.1)
        self._test_sit(20000.0, 'married', 0.0, 3.0, 'quarterly', date(2020, 1, 1), 876.0)
