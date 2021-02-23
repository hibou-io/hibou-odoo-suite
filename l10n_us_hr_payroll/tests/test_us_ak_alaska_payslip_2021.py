# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date
from .common import TestUsPayslip


class TestUsAKPayslip(TestUsPayslip):
    # TAXES AND RATES
    AK_UNEMP_MAX_WAGE = 43600.00
    AK_UNEMP = 2.57
    AK_UNEMP_EE = 0.5

    def test_2021_taxes(self):
        self._test_er_suta('AK', self.AK_UNEMP, date(2021, 1, 1), wage_base=self.AK_UNEMP_MAX_WAGE)
        self._test_ee_suta('AK', self.AK_UNEMP_EE, date(2021, 1, 1), wage_base=self.AK_UNEMP_MAX_WAGE)
