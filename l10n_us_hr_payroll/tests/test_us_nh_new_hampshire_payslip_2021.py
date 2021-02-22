# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date
from .common import TestUsPayslip


class TestUsNHPayslip(TestUsPayslip):
    # TAXES AND RATES
    NH_UNEMP_MAX_WAGE = 14000.00
    NH_UNEMP = 2.7

    def test_2021_taxes(self):
        self._test_er_suta('NH', self.NH_UNEMP, date(2021, 1, 1), wage_base=self.NH_UNEMP_MAX_WAGE)
