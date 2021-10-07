# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsNCPayslip(TestUsPayslip):
    ###
    #    2020 Taxes and Rates
    ###
    NC_UNEMP_MAX_WAGE = 25200.0
    NC_UNEMP = 1.0
    NC_INC_TAX = 0.0535
    # Example based on https://files.nc.gov/ncdor/documents/files/NC-30_book_Web_1-16-19_v4_Final.pdf 
    def _test_sit(self, wage, filing_status, allowances, additional_withholding, schedule_pay, date_start, expected_withholding):

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('NC'),
                                        nc_nc4_sit_filing_status=filing_status,
                                        nc_nc4_sit_allowances=allowances,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding if filing_status else 0.0)

    def test_2020_taxes_example(self):
        self._test_er_suta('NC', self.NC_UNEMP, date(2020, 1, 1), wage_base=self.NC_UNEMP_MAX_WAGE)
        self._test_sit(20000.0, 'single', 1, 100.0, 'weekly', date(2020, 1, 1), 1156.0)
        self._test_sit(5000.0, 'married', 1, 0.0, 'weekly', date(2020, 1, 1), 254.0)
        self._test_sit(4000.0, 'head_household', 1, 5.0, 'semi-monthly', date(2020, 1, 1), 177.0)
        self._test_sit(7000.0, '', 1, 5.0, 'monthly', date(2020, 1, 1), 0.0)
