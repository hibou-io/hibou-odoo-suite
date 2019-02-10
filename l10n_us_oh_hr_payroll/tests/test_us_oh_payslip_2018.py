from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip
from odoo.addons.l10n_us_hr_payroll.models.l10n_us_hr_payroll import USHrContract


class TestUsOhPayslip(TestUsPayslip):
    ###
    #    Taxes and Rates
    ###
    OH_UNEMP_MAX_WAGE = 9500.0
    OH_UNEMP = -2.7 / 100.0

    def test_2018_taxes(self):
        salary = 5000.0

        # For formula here
        # http://www.tax.ohio.gov/Portals/0/employer_withholding/August2015Rates/WTH_OptionalComputerFormula_073015.pdf
        tw = salary * 12  # = 60000
        wd = ((tw - 40000) * 0.035 + 900) / 12 * 1.112

        employee = self._createEmployee()

        contract = self._createContract(employee, salary, struct_id=self.ref('l10n_us_oh_hr_payroll.hr_payroll_salary_structure_us_oh_employee'))

        self._log('2017 Ohio tax last payslip:')
        payslip = self._createPayslip(employee, '2017-12-01', '2017-12-31')
        payslip.compute_sheet()
        process_payslip(payslip)

        self._log('2018 Ohio tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_OH_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_OH_UNEMP'], cats['WAGE_US_OH_UNEMP'] * self.OH_UNEMP)
        self.assertPayrollEqual(cats['EE_US_OH_INC_WITHHOLD'], -wd)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_oh_unemp_wages = self.OH_UNEMP_MAX_WAGE - salary if (self.OH_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2018 Ohio tax second payslip:')
        payslip = self._createPayslip(employee, '2018-02-01', '2018-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_OH_UNEMP'], remaining_oh_unemp_wages)
        self.assertPayrollEqual(cats['ER_US_OH_UNEMP'], remaining_oh_unemp_wages * self.OH_UNEMP)

    def test_2018_taxes_with_external(self):
        salary = 5000.0
        external_wages = 6000.0

        employee = self._createEmployee()

        contract = self._createContract(employee, salary, external_wages=external_wages,
                                        struct_id=self.ref('l10n_us_oh_hr_payroll.hr_payroll_salary_structure_us_oh_employee'))

        self._log('2018 Ohio_external tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_OH_UNEMP'], self.OH_UNEMP_MAX_WAGE - external_wages)
        self.assertPayrollEqual(cats['ER_US_OH_UNEMP'], cats['WAGE_US_OH_UNEMP'] * self.OH_UNEMP)

    def test_2018_taxes_with_state_exempt(self):
        salary = 5000.0
        external_wages = 6000.0

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, external_wages=external_wages, struct_id=self.ref(
            'l10n_us_oh_hr_payroll.hr_payroll_salary_structure_us_oh_employee'), futa_type=USHrContract.FUTA_TYPE_BASIC)

        self._log('2018 Ohio exempt tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        # FUTA_TYPE_BASIC
        self.assertPayrollEqual(cats.get('WAGE_US_OH_UNEMP', 0.0), 0.0)
        self.assertPayrollEqual(cats.get('ER_US_OH_UNEMP', 0.0), cats.get('WAGE_US_OH_UNEMP', 0.0) * 0.0)
