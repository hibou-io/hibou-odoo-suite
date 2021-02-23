# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date
from .common import TestUsPayslip


class TestUsWYPayslip(TestUsPayslip):
    # TAXES AND RATES
    WY_UNEMP_MAX_WAGE = 27300.00
    WY_UNEMP = 8.5

    def test_2021_taxes(self):
        self._test_er_suta('WY', self.WY_UNEMP, date(2021, 1, 1), wage_base=self.WY_UNEMP_MAX_WAGE)
