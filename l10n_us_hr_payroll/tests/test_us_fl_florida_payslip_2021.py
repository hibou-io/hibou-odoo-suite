# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date
from .common import TestUsPayslip


class TestUsFlPayslip(TestUsPayslip):
    ###
    #   2021 Taxes and Rates
    ###
    FL_UNEMP_MAX_WAGE = 7000.0
    FL_UNEMP = 2.9

    def test_2021_taxes(self):
        # Only has state unemployment
        self._test_er_suta('FL', self.FL_UNEMP, date(2021, 1, 1), wage_base=self.FL_UNEMP_MAX_WAGE)
