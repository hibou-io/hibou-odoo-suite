# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date
from .common import TestUsPayslip

class TestUsTXPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    TX_UNEMP_MAX_WAGE = 9000.0
    TX_UNEMP = 2.7
    TX_OA = 0.0
    TX_ETIA = 0.1

    def test_2020_taxes(self):
        combined_rate = self.TX_UNEMP + self.TX_OA + self.TX_ETIA
        self._test_er_suta('TX', combined_rate, date(2020, 1, 1), wage_base=self.TX_UNEMP_MAX_WAGE)
