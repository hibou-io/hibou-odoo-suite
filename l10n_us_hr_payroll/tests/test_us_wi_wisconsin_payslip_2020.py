# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsWIPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    WI_UNEMP_MAX_WAGE = 14000.0
    WI_UNEMP = 3.05
    # Calculation based on example https://www.revenue.wi.gov/DOR%20Publications/pb166.pdf

    def _test_sit(self, wage, filing_status, exemption, additional_withholding, exempt, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('WI'),
                                        wi_wt4_sit_filing_status=filing_status,
                                        wi_wt4_sit_exemptions=exemption,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        state_income_tax_exempt=exempt,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollAlmostEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('WI', self.WI_UNEMP, date(2020, 1, 1), wage_base=self.WI_UNEMP_MAX_WAGE)
        self._test_sit(300, 'single', 1, 0, False, 'weekly', date(2020, 1, 1), 7.21)
        self._test_sit(700, 'married', 3, 0, False, 'bi-weekly', date(2020, 1, 1), 13.35)
        self._test_sit(7000, 'single', 1, 10, True, 'bi-weekly', date(2020, 1, 1), 0.00)
        self._test_sit(10000, 'married', 3, 10, False, 'bi-weekly', date(2020, 1, 1), 633.65)
        # ((48000 - 26227) * (7.0224 /100) + 1073.55 - 44) / 12
        self._test_sit(4000, 'single', 2, 0, False, 'monthly', date(2020, 1, 1), 213.21)
