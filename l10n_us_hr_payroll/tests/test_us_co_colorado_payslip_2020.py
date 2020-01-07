# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsCOPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    CO_UNEMP_MAX_WAGE = 13600.0
    CO_UNEMP = 1.7

    def _test_sit(self, wage, filing_status, additional_withholding, schedule_pay,  date_start, expected_withholding, state_income_tax_exempt=False):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('CO'),
                                        fed_941_fit_w4_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        state_income_tax_exempt=state_income_tax_exempt,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('CO', self.CO_UNEMP, date(2020, 1, 1), wage_base=self.CO_UNEMP_MAX_WAGE)
        self._test_sit(5000.0, 'married', 0.0, 'semi-monthly', date(2020, 1, 1), 216.07)
        self._test_sit(800.0, 'single', 0.0, 'weekly', date(2020, 1, 1), 33.48)
        self._test_sit(20000.0, 'married', 0.0, 'quarterly', date(2020, 1, 1), 833.4)
        self._test_sit(20000.0, 'married', 10.0, 'quarterly', date(2020, 1, 1), 843.4)
        self._test_sit(20000.0, 'married', 0.0, 'quarterly', date(2020, 1, 1), 0.0, True)
        self._test_sit(800.0, '', 0.0, 'weekly', date(2020, 1, 1), 0.00)
