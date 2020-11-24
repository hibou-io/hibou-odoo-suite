# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsNJPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    NJ_UNEMP_MAX_WAGE = 35300.0  # Note that this is used for SDI and FLI as well

    ER_NJ_UNEMP = 2.6825
    EE_NJ_UNEMP = 0.3825

    ER_NJ_SDI = 0.5
    EE_NJ_SDI = 0.26

    ER_NJ_WF = 0.1175
    EE_NJ_WF = 0.0425

    ER_NJ_FLI = 0.0
    EE_NJ_FLI = 0.16

    def _test_sit(self, wage, filing_status, allowances, schedule_pay,  date_start, expected_withholding, rate_table=False):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('NJ'),
                                        nj_njw4_sit_filing_status=filing_status,
                                        nj_njw4_sit_allowances=allowances,
                                        state_income_tax_additional_withholding=0.0,
                                        nj_njw4_sit_rate_table=rate_table,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertPayrollAlmostEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding if filing_status else 0.0)
  
    def test_2020_taxes_example1(self):
        combined_er_rate = self.ER_NJ_UNEMP + self.ER_NJ_FLI + self.ER_NJ_SDI + self.ER_NJ_WF
        self._test_er_suta('NJ', combined_er_rate, date(2020, 1, 1), wage_base=self.NJ_UNEMP_MAX_WAGE)
        combined_ee_rate = self.EE_NJ_UNEMP + self.EE_NJ_FLI + self.EE_NJ_SDI + self.EE_NJ_WF
        self._test_ee_suta('NJ', combined_ee_rate, date(2020, 1, 1), wage_base=self.NJ_UNEMP_MAX_WAGE, relaxed=True)
        # these expected values come from https://www.state.nj.us/treasury/taxation/pdf/current/njwt.pdf
        self._test_sit(300.0, 'single', 1, 'weekly', date(2020, 1, 1), 4.21)
        self._test_sit(375.0, 'married_separate', 3, 'weekly', date(2020, 1, 1), 4.76)
        self._test_sit(1400.0, 'head_household', 3, 'weekly', date(2020, 1, 1), 27.60)
        self._test_sit(1400.0, '', 3, 'weekly', date(2020, 1, 1), 0.00)
        self._test_sit(2500.0, 'single', 3, 'bi-weekly', date(2020, 1, 1), 82.66)
        self._test_sit(15000.0, 'married_joint', 2, 'monthly', date(2020, 1, 1), 844.85)
