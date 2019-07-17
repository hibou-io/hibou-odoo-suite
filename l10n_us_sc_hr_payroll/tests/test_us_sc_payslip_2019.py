from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip
from odoo.addons.l10n_us_hr_payroll.models.l10n_us_hr_payroll import USHrContract


class TestUsSCPayslip(TestUsPayslip):

    #    Taxes and Rates
    SC_UNEMP_MAX_WAGE = 14000.0
    US_SC_UNEMP = -1.09 / 100
    US_SC_exemption_amount = 2510.00

    def test_2019_taxes_weekly(self):
        # We will hand calculate the amount to test for state withholding.
        schedule_pay = 'weekly'
        salary = 50000.00  # Employee is paid 50000 per week to be in top tax bracket
        exemptions = 2
        # Calculate annual wages
        annual = 50000 * 52.0
        # From our annual we deduct personal exemption amounts.
        # We deduct 2510.00 per exemption. Since we have two exemptions:
        personal_exemption = self.US_SC_exemption_amount * exemptions  # 5020.0
        # From annual, we will also deduct a standard_deduction of 10% up to 3470.00 if 1 or more exemptions
        standard_deduction = (10.0 / 100.0) * 3470.00
        taxable_income = annual - personal_exemption - standard_deduction  # 2594633.0
        # We then calculate the amounts off the SC tax pdf tables.
        # 2594633.0 is in the highest bracket
        test_amt = ((taxable_income - 12250) * (7.0 / 100.0)) + 467.95
        # test_amt = 181234.76000000004
        # Make it per period then negative
        test_amt = (test_amt / 52.0)  # Divided by 52 since it is weekly.
        # test_amt = 3485.2838461538468
        test_amt = -test_amt

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref('l10n_us_sc_hr_payroll.hr_payroll_salary_structure_us_sc_employee'),
                                        schedule_pay=schedule_pay)
        contract.w4_allowances = exemptions

        self._log('2019 South Carolina tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_SC_UNEMP'], self.SC_UNEMP_MAX_WAGE)
        self.assertPayrollEqual(cats['ER_US_SC_UNEMP'], cats['WAGE_US_SC_UNEMP'] * self.US_SC_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SC_INC_WITHHOLD'], test_amt)

        process_payslip(payslip)

        remaining_SC_UNEMP_wages = self.SC_UNEMP_MAX_WAGE - annual if (annual < self.SC_UNEMP_MAX_WAGE) \
            else 0.00

        self._log('2019 South Carolina tax second payslip:')

        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertEqual(0.0, remaining_SC_UNEMP_wages)
        self.assertPayrollEqual(cats['ER_US_SC_UNEMP'], remaining_SC_UNEMP_wages * self.US_SC_UNEMP)

    def test_2019_taxes_with_external(self):
        salary = 5000.0
        external_wages = 30000.0

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        salary,
                                        external_wages=external_wages,
                                        struct_id=self.ref('l10n_us_sc_hr_payroll.hr_payroll_salary_structure_us_sc_employee'))

        self._log('2019 South Carolina_external tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_SC_UNEMP'], 0)
        self.assertPayrollEqual(cats['ER_US_SC_UNEMP'], cats['WAGE_US_SC_UNEMP'] * self.US_SC_UNEMP)

    def test_2019_taxes_filing_status(self):
        salary = 20000.00  # Wages per pay period
        schedule_pay = 'monthly'
        annual = salary * 12
        w4_filing_status = 'married'
        allowances = 1
        # Hand Calculations
        personal_exemption = 2510.00
        standard_deduction = (10.0 / 100.0) * 3470.00
        taxable = annual - personal_exemption - standard_deduction
        # taxable = 237143.0
        test_amt = ((taxable - 12250) * (7.0 / 100.0)) + 467.95  # 16210.460000000003
        test_amt = test_amt / 12.0  # Put it into monthly -> 1350.871666666667
        # Make it negative
        test_amt = -test_amt

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref('l10n_us_sc_hr_payroll.hr_payroll_salary_structure_us_sc_employee'))
        contract.w4_allowances = allowances
        contract.w4_filing_status = w4_filing_status

        self._log('2019 South Carolina tax first payslip: ')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_SC_UNEMP'], self.SC_UNEMP_MAX_WAGE)
        self.assertPayrollEqual(cats['ER_US_SC_UNEMP'], cats['WAGE_US_SC_UNEMP'] * self.US_SC_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SC_INC_WITHHOLD'], test_amt)

        process_payslip(payslip)

        # Create a 2nd payslip
        remaining_SC_UNEMP_wages = self.SC_UNEMP_MAX_WAGE - salary if (salary < self.SC_UNEMP_MAX_WAGE) \
            else 0.00

        self._log('2019 South Carolina tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertEqual(0.0, remaining_SC_UNEMP_wages)
        self.assertPayrollEqual(cats['ER_US_SC_UNEMP'], remaining_SC_UNEMP_wages * self.US_SC_UNEMP)

