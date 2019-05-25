from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip


class TestUsMsPayslip(TestUsPayslip):
    # Calculations from https://www.dor.ms.gov/Documents/Computer%20Payroll%20Accounting%201-2-19.pdf
    MS_UNEMP = -1.2 / 100.0

    def test_2019_taxes_one(self):
        salary = 1250.0
        ms_89_350_exemption = 11000.0

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, struct_id=self.ref('l10n_us_ms_hr_payroll.hr_payroll_salary_structure_us_ms_employee'),
                                        schedule_pay='semi-monthly')
        contract.ms_89_350_filing_status = 'head_of_household'
        contract.ms_89_350_exemption = ms_89_350_exemption

        self._log('2019 Mississippi tax single first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_MS_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_MS_UNEMP'], cats['WAGE_US_MS_UNEMP'] * self.MS_UNEMP)

        STDED = 3400.0  # Head of Household
        AGP = salary * 24  # Semi-Monthly
        TI = AGP - (ms_89_350_exemption + STDED)
        self.assertPayrollEqual(TI, 15600.0)
        TAX = ((TI - 10000) * 0.05) + 290  # Over 10,000
        self.assertPayrollEqual(TAX, 570.0)

        ms_withhold = round(TAX / 24)  # Semi-Monthly
        self.assertPayrollEqual(cats['EE_US_MS_INC_WITHHOLD'], -ms_withhold)

    def test_2019_taxes_one_exempt(self):
        salary = 1250.0
        ms_89_350_exemption = 11000.0

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, struct_id=self.ref('l10n_us_ms_hr_payroll.hr_payroll_salary_structure_us_ms_employee'),
                                        schedule_pay='semi-monthly')
        contract.ms_89_350_filing_status = ''
        contract.ms_89_350_exemption = ms_89_350_exemption

        self._log('2019 Mississippi tax single first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats.get('EE_US_MS_INC_WITHHOLD', 0.0), 0.0)

    def test_2019_taxes_additional(self):
        salary = 1250.0
        ms_89_350_exemption = 11000.0
        additional = 40.0

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, struct_id=self.ref('l10n_us_ms_hr_payroll.hr_payroll_salary_structure_us_ms_employee'),
                                        schedule_pay='semi-monthly')
        contract.ms_89_350_filing_status = 'head_of_household'
        contract.ms_89_350_exemption = ms_89_350_exemption
        contract.ms_89_350_additional_withholding = additional

        self._log('2019 Mississippi tax single first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_MS_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_MS_UNEMP'], cats['WAGE_US_MS_UNEMP'] * self.MS_UNEMP)

        STDED = 3400.0  # Head of Household
        AGP = salary * 24  # Semi-Monthly
        TI = AGP - (ms_89_350_exemption + STDED)
        self.assertPayrollEqual(TI, 15600.0)
        TAX = ((TI - 10000) * 0.05) + 290  # Over 10,000
        self.assertPayrollEqual(TAX, 570.0)

        ms_withhold = round(TAX / 24)  # Semi-Monthly
        self.assertPayrollEqual(cats['EE_US_MS_INC_WITHHOLD'], -ms_withhold + -additional)
