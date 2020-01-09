# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date
from .common import TestUsPayslip


class TestUsMsPayslip(TestUsPayslip):
    # Calculations from https://www.dor.ms.gov/Documents/Computer%20Payroll%20Accounting%201-2-19.pdf
    MS_UNEMP = 1.2
    MS_UNEMP_MAX_WAGE = 14000.0

    def test_2020_taxes_one(self):
        self._test_er_suta('MS', self.MS_UNEMP, date(2020, 1, 1), wage_base=self.MS_UNEMP_MAX_WAGE)

        salary = 1250.0
        ms_89_350_exemption = 11000.0

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MS'),
                                        ms_89_350_sit_filing_status='head_of_household',
                                        ms_89_350_sit_exemption_value=ms_89_350_exemption,
                                        state_income_tax_additional_withholding=0.0,
                                        schedule_pay='semi-monthly')

        self._log('2020 Mississippi tax single first payslip:')
        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        STDED = 3400.0  # Head of Household
        AGP = salary * 24  # Semi-Monthly
        TI = AGP - (ms_89_350_exemption + STDED)
        self.assertPayrollEqual(TI, 15600.0)
        TAX = ((TI - 10000) * 0.05) + 260  # Over 10,000
        self.assertPayrollEqual(TAX, 540.0)

        ms_withhold = round(TAX / 24)  # Semi-Monthly
        self.assertPayrollEqual(cats['EE_US_SIT'], -ms_withhold)

    def test_2020_taxes_one_exempt(self):
        salary = 1250.0
        ms_89_350_exemption = 11000.0

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MS'),
                                        ms_89_350_sit_filing_status='',
                                        ms_89_350_sit_exemption_value=ms_89_350_exemption,
                                        state_income_tax_additional_withholding=0.0,
                                        schedule_pay='semi-monthly')

        self._log('2020 Mississippi tax single first payslip:')
        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), 0.0)

    def test_2020_taxes_additional(self):
        salary = 1250.0
        ms_89_350_exemption = 11000.0
        additional = 40.0

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MS'),
                                        ms_89_350_sit_filing_status='single',
                                        ms_89_350_sit_exemption_value=ms_89_350_exemption,
                                        state_income_tax_additional_withholding=additional,
                                        schedule_pay='monthly')

        self._log('2020 Mississippi tax single first payslip:')
        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        STDED = 2300.0  # Single
        AGP = salary * 12  # Monthly
        TI = AGP - (ms_89_350_exemption + STDED)
        self.assertPayrollEqual(TI, 1700.0)
        TAX = ((TI - 3000) * 0.03)
        self.assertPayrollEqual(TAX, -39.0)

        ms_withhold = round(TAX / 12)  # Monthly
        self.assertTrue(ms_withhold <= 0.0)
        self.assertPayrollEqual(cats['EE_US_SIT'], -40.0) # only additional

        # Test with higher wage
        salary = 1700.0
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MS'),
                                        ms_89_350_sit_filing_status='single',
                                        ms_89_350_sit_exemption_value=ms_89_350_exemption,
                                        state_income_tax_additional_withholding=additional,
                                        schedule_pay='monthly')
        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        STDED = 2300.0  # Single
        AGP = salary * 12  # Monthly
        TI = AGP - (ms_89_350_exemption + STDED)
        self.assertPayrollEqual(TI, 7100.0)
        TAX = ((TI - 5000) * 0.04) + 60.0
        self.assertPayrollEqual(TAX, 144.0)

        ms_withhold = round(TAX / 12)  # Monthly
        self.assertPayrollEqual(ms_withhold, 12.0)
        self.assertPayrollEqual(cats['EE_US_SIT'], -(ms_withhold + additional))
