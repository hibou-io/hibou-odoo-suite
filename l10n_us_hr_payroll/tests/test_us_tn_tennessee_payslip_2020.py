# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date
from .common import TestUsPayslip


class TestUsTNPayslip(TestUsPayslip):
    # TAXES AND RATES
    TN_UNEMP_MAX_WAGE = 7000.00
    TN_UNEMP = 2.7

    def test_2020_taxes(self):
        self._test_er_suta('TN', self.TN_UNEMP, date(2020, 1, 1), wage_base=self.TN_UNEMP_MAX_WAGE)
