from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip
from odoo.addons.l10n_us_hr_payroll.models.l10n_us_hr_payroll import USHrContract


class TestUsSCPayslip(TestUsPayslip):
    ###
    #    Taxes and Rates
    ###
    SC_UNEMP_MAX_WAGE = 14000.0
    US_SC_UNEMP = -1.09 / 100

    def test_2019_taxes(self):
        salary = 10000
        exemptions = 2

        employee = self._createEmployee()
        contract = self._createContract(employee, salary,
                                        struct_id=self.ref('l10n_us_sc_hr_payroll.hr_payroll_salary_structure_us_sc_employee'))
        contract.w4_allowances = exemptions

        self._log('2019 South Carolina tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_SC_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_SC_UNEMP'], cats['WAGE_US_SC_UNEMP'] * self.US_SC_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SC_INC_WITHHOLD'], cats['EE_US_FED_INC_WITHHOLD'])

        process_payslip(payslip)

        remaining_SC_UNEMP_wages = self.SC_UNEMP_MAX_WAGE - salary if (self.SC_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        # Testing Additional Income Tax Withholding
        self._log('2019 South Carolina tax second payslip:')
        additional_wh = 40.0
        contract.w4_additional_withholding = additional_wh
        original_witholding = cats['EE_US_SC_INC_WITHHOLD']
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_SC_UNEMP'], remaining_SC_UNEMP_wages)
        self.assertPayrollEqual(cats['ER_US_SC_UNEMP'], remaining_SC_UNEMP_wages * self.US_SC_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SC_INC_WITHHOLD'], original_witholding - additional_wh)

    def test_2019_taxes_with_external(self):
        salary = 5000.0
        external_wages = 30000.0

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, external_wages=external_wages,
                                        struct_id=self.ref('l10n_us_sc_hr_payroll.hr_payroll_salary_structure_us_sc_employee'))

        self._log('2019 South Carolina_external tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_SC_UNEMP'], 0)
        self.assertPayrollEqual(cats['ER_US_SC_UNEMP'], cats['WAGE_US_SC_UNEMP'] * self.US_SC_UNEMP)

    def test_2019_taxes_filing_status(self):
        salary = 4000.0
        w4_filing_status = 'married'

        allowances = 1

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, struct_id=self.ref(
            'l10n_us_sc_hr_payroll.hr_payroll_salary_structure_us_sc_employee'))
        contract.w4_allowances = allowances
        contract.w4_filing_status = w4_filing_status

        self._log('2019 South Carolina tax first payslip: ')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_SC_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_SC_UNEMP'], cats['WAGE_US_SC_UNEMP'] * self.US_SC_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SC_INC_WITHHOLD'], cats['EE_US_FED_INC_WITHHOLD'])

        process_payslip(payslip)

        # Create a 2nd payslip
        remaining_SC_UNEMP_wages = self.SC_UNEMP_MAX_WAGE - salary if (self.SC_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2019 South Carolina tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_SC_UNEMP'], remaining_SC_UNEMP_wages)
        self.assertPayrollEqual(cats['ER_US_SC_UNEMP'], remaining_SC_UNEMP_wages * self.US_SC_UNEMP)

    def test_additional_withholding(self):
        salary = 4000.0
        additional_wh = 40.0
        allowances = 1

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref('l10n_us_sc_hr_payroll.hr_payroll_salary_structure_us_sc_employee')
                                        )
        contract.w4_addition_withholding = additional_wh
        contract.w4_allowances = allowances


        self._log('2019 South Carolina tax first payslip: ')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_SC_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_SC_UNEMP'], cats['WAGE_US_SC_UNEMP'] * self.US_SC_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SC_INC_WITHHOLD'], cats['EE_US_FED_INC_WITHHOLD'])

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums
        remaining_SC_UNEMP_wages = self.SC_UNEMP_MAX_WAGE - salary if (self.SC_UNEMP_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2019 South Carolina tax second payslip weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_SC_UNEMP'], remaining_SC_UNEMP_wages)
        self.assertPayrollEqual(cats['ER_US_SC_UNEMP'], remaining_SC_UNEMP_wages * self.US_SC_UNEMP)
