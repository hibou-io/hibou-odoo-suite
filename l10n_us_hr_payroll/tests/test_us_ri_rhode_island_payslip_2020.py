# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsRIPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    RI_UNEMP_MAX_WAGE = 24000.0
    RI_UNEMP = 1.06
    # Calculation based on example http://www.tax.ri.gov/forms/2020/Withholding/2020%20Withhholding%20Tax%20Booklet.pdf

    def _test_sit(self, wage, allowances, additional_withholding, exempt, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('RI'),
                                        ri_w4_sit_allowances=allowances,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        state_income_tax_exempt=exempt,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('RI', self.RI_UNEMP, date(2020, 1, 1), wage_base=self.RI_UNEMP_MAX_WAGE)
        self._test_sit(2195, 1, 0, False, 'weekly', date(2020, 1, 1), 90.80)
        self._test_sit(1800, 2, 10, True, 'weekly', date(2020, 1, 1), 0.00)
        self._test_sit(10000, 1, 0, False, 'bi-weekly', date(2020, 1, 1), 503.15)
        self._test_sit(18000, 2, 0, False, 'monthly', date(2020, 1, 1), 860.54)
        self._test_sit(18000, 2, 10, False, 'monthly', date(2020, 1, 1), 870.55)
