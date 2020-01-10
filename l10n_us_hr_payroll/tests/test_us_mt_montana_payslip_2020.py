# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date
from .common import TestUsPayslip, process_payslip


class TestUsMtPayslip(TestUsPayslip):
    # Calculations from https://app.mt.gov/myrevenue/Endpoint/DownloadPdf?yearId=705
    MT_UNEMP_WAGE_MAX = 34100.0
    MT_UNEMP = 1.18
    MT_UNEMP_AFT = 0.13

    def test_2020_taxes_one(self):
        combined_rate = self.MT_UNEMP + self.MT_UNEMP_AFT  # Combined for test as they both go to the same category and have the same cap
        self._test_er_suta('MT', combined_rate, date(2020, 1, 1), wage_base=self.MT_UNEMP_WAGE_MAX)

    # TODO Montana Incometax rates for 2020 when released
