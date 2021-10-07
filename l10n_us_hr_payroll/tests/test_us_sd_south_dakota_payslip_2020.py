# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date
from .common import TestUsPayslip


class TestUsSDPayslip(TestUsPayslip):
    # TAXES AND RATES
    SD_UNEMP_MAX_WAGE = 15000.00
    SD_UNEMP = 1.75

    def test_2020_taxes(self):
        self._test_er_suta('SD', self.SD_UNEMP, date(2020, 1, 1), wage_base=self.SD_UNEMP_MAX_WAGE)
