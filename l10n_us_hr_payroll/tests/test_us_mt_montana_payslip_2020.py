# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsMtPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    MT_UNEMP_WAGE_MAX = 34100.0
    MT_UNEMP = 1.18
    MT_UNEMP_AFT = 0.13

    # Calculations from https://app.mt.gov/myrevenue/Endpoint/DownloadPdf?yearId=705
    def _test_sit(self, wage, additional_withholding, exemptions, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('MT'),
                                        state_income_tax_additional_withholding=additional_withholding,
                                        mt_mw4_sit_exemptions=exemptions,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_one(self):
        combined_rate = self.MT_UNEMP + self.MT_UNEMP_AFT  # Combined for test as they both go to the same category and have the same cap
        self._test_er_suta('MT', combined_rate, date(2020, 1, 1), wage_base=self.MT_UNEMP_WAGE_MAX)
        self._test_sit(550.0, 0.0, 5.0, 'semi-monthly', date(2020, 1, 1), 3.0)
        self._test_sit(2950.0, 10.0, 2.0, 'bi-weekly', date(2020, 1, 1), 162.0)
        self._test_sit(5000.0, 0.0, 1.0, 'monthly', date(2020, 1, 1), 256.0)
        self._test_sit(750.0, 0.0, 1.0, 'weekly', date(2020, 1, 1), 34.0)
