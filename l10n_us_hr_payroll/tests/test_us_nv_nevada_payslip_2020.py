# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date
from .common import TestUsPayslip


class TestUsNVPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    NV_UNEMP_MAX_WAGE = 32500.0
    NV_UNEMP = 2.95

    def test_2020_taxes(self):
        # Only has state unemployment
        self._test_er_suta('NV', self.NV_UNEMP, date(2020, 1, 1), wage_base=self.NV_UNEMP_MAX_WAGE)
