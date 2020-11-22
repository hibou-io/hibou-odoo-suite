# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsCAPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    CA_UNEMP_MAX_WAGE = 7000.0  # Note that this is used for SDI and FLI as well
    CA_UIT = 3.4
    CA_ETT = 0.1
    CA_SDI = 1.0

    def _test_sit(self, wage, filing_status, allowances, additional_allowances, additional_withholding, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('CA'),
                                        ca_de4_sit_filing_status=filing_status,
                                        ca_de4_sit_allowances=allowances,
                                        ca_de4_sit_additional_allowances=additional_allowances,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertPayrollAlmostEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding if filing_status else 0.0)
  
    def test_2020_taxes_example1(self):
        combined_er_rate = self.CA_UIT + self.CA_ETT
        self._test_er_suta('CA', combined_er_rate, date(2020, 1, 1), wage_base=self.CA_UNEMP_MAX_WAGE)
        self._test_ee_suta('CA', self.CA_SDI, date(2020, 1, 1), wage_base=self.CA_UNEMP_MAX_WAGE, relaxed=True)
        # these expected values come from https://www.edd.ca.gov/pdf_pub_ctr/20methb.pdf
        self._test_sit(210.0, 'single', 1, 0, 0, 'weekly', date(2020, 1, 1), 0.00)
        self._test_sit(1250.0, 'married', 2, 1, 0, 'bi-weekly', date(2020, 1, 1), 1.23)
        self._test_sit(4100.0, 'married', 5, 0, 0, 'monthly', date(2020, 1, 1), 1.5)
        self._test_sit(800.0, 'head_household', 3, 0, 0, 'weekly', date(2020, 1, 1), 2.28)
        self._test_sit(1800.0, 'married', 4, 0, 0, 'semi-monthly', date(2020, 1, 1), 0.84)
        self._test_sit(45000.0, 'married', 4, 0, 0, 'annually', date(2020, 1, 1), 59.78)
        self._test_sit(45000.0, 'married', 4, 0, 20.0, 'annually', date(2020, 1, 1), 79.78)
        self._test_sit(6000.0, '', 4, 0, 20.0, 'annually', date(2020, 1, 1), 0.00)
