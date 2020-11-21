# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta
from .common import TestUsPayslip


class TestUsNMPayslip(TestUsPayslip):
    ###
    #   2020 Taxes and Rates
    ###
    NM_UNEMP_MAX_WAGE = 25800.0
    NM_UNEMP = 1.0
    # Calculation based on section 17. https://s3.amazonaws.com/realFile34821a95-73ca-43e7-b06d-fad20f5183fd/a9bf1098-533b-4a3d-806a-4bf6336af6e4?response-content-disposition=filename%3D%22FYI-104+-+New+Mexico+Withholding+Tax+-+Effective+January+1%2C+2020.pdf%22&response-content-type=application%2Fpdf&AWSAccessKeyId=AKIAJBI25DHBYGD7I7TA&Signature=feu%2F1oJvU6BciRfKcoR0iNxoVZE%3D&Expires=1585159702

    def _test_sit(self, wage, filing_status, additional_withholding, schedule_pay,  date_start, expected_withholding):
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('NM'),
                                        fed_941_fit_w4_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        schedule_pay=schedule_pay)
        payslip = self._createPayslip(employee, date_start, date_start + timedelta(days=7))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self._log('Computed period tax: ' + str(expected_withholding))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -expected_withholding)

    def test_2020_taxes_example(self):
        self._test_er_suta('NM', self.NM_UNEMP, date(2020, 1, 1), wage_base=self.NM_UNEMP_MAX_WAGE)
        self._test_sit(1000.0, 'married', 0.0, 'weekly', date(2020, 1, 1), 29.47)
        self._test_sit(1000.0, 'married', 10.0, 'weekly', date(2020, 1, 1), 39.47)
        self._test_sit(25000.0, 'single', 0.0, 'bi-weekly', date(2020, 1, 1), 1202.60)
        self._test_sit(25000.0, 'married_as_single', 0.0, 'monthly', date(2020, 1, 1), 1152.95)
        self._test_sit(4400.0, '', 0.0, 'monthly', date(2020, 1, 1), 0.00)
