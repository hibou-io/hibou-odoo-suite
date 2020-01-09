# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip


class TestUsMsPayslip(TestUsPayslip):
    # Calculations from https://www.dor.ms.gov/Documents/Computer%20Payroll%20Accounting%201-2-19.pdf
    MS_UNEMP = -1.2 / 100.0

    def test_2019_taxes_one(self):
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

        self._log('2019 Mississippi tax single first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.MS_UNEMP)

        STDED = 3400.0  # Head of Household
        AGP = salary * 24  # Semi-Monthly
        TI = AGP - (ms_89_350_exemption + STDED)
        self.assertPayrollEqual(TI, 15600.0)
        TAX = ((TI - 10000) * 0.05) + 290  # Over 10,000
        self.assertPayrollEqual(TAX, 570.0)

        ms_withhold = round(TAX / 24)  # Semi-Monthly
        self.assertPayrollEqual(cats['EE_US_SIT'], -ms_withhold)

    def test_2019_taxes_one_exempt(self):
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

        self._log('2019 Mississippi tax single first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), 0.0)

    def test_2019_taxes_additional(self):
        salary = 1250.0
        ms_89_350_exemption = 11000.0
        additional = 40.0

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MS'),
                                        ms_89_350_sit_filing_status='head_of_household',
                                        ms_89_350_sit_exemption_value=ms_89_350_exemption,
                                        state_income_tax_additional_withholding=additional,
                                        schedule_pay='semi-monthly')

        self._log('2019 Mississippi tax single first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.MS_UNEMP)

        STDED = 3400.0  # Head of Household
        AGP = salary * 24  # Semi-Monthly
        TI = AGP - (ms_89_350_exemption + STDED)
        self.assertPayrollEqual(TI, 15600.0)
        TAX = ((TI - 10000) * 0.05) + 290  # Over 10,000
        self.assertPayrollEqual(TAX, 570.0)

        ms_withhold = round(TAX / 24)  # Semi-Monthly
        self.assertPayrollEqual(cats['EE_US_SIT'], -ms_withhold + -additional)
