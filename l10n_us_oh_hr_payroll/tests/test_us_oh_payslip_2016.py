# -*- coding: utf-8 -*-

from openerp.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip
from openerp.addons.l10n_us_hr_payroll.l10n_us_hr_payroll import USHrContract


class TestUsOhPayslip(TestUsPayslip):
    ###
    #   2016 Taxes and Rates
    ###

    def test_2016_taxes(self):
        salary = 5000.0

        ## tax maximums
        OH_UNEMP_MAX_WAGE = 9000.0

        ## For formula here
        # http://www.tax.ohio.gov/Portals/0/employer_withholding/August2015Rates/WTH_OptionalComputerFormula_073015.pdf
        TW = salary * 12  # = 60000
        WD = ((TW - 40000) * 0.035 + 900) / 12 * 1.112


        employee = self._createEmployee()
        employee.company_id.oh_unemp_rate_2016 = 2.7

        contract = self._createContract(employee, salary, struct_id=self.ref('l10n_us_oh_hr_payroll.hr_payroll_salary_structure_us_oh_employee'))

        ## tax rates
        OH_UNEMP = contract.oh_unemp_rate(2016) / -100.0

        self._log('2016 Ohio tax first payslip:')
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['OH_UNEMP_WAGES'], salary)
        self.assertPayrollEqual(cats['OH_UNEMP'], cats['OH_UNEMP_WAGES'] * OH_UNEMP)
        self.assertPayrollEqual(cats['OH_INC_WITHHOLD'], -WD)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_oh_unemp_wages = OH_UNEMP_MAX_WAGE - salary if (OH_UNEMP_MAX_WAGE - 2*salary < salary) else salary

        self._log('2016 Ohio tax second payslip:')
        payslip = self._createPayslip(employee, '2016-02-01', '2016-02-29')  # 2016 is a leap year

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['OH_UNEMP_WAGES'], remaining_oh_unemp_wages)
        self.assertPayrollEqual(cats['OH_UNEMP'], remaining_oh_unemp_wages * OH_UNEMP)


    def test_2016_taxes_with_external(self):
        salary = 5000.0
        external_wages = 6000.0

        employee = self._createEmployee()
        employee.company_id.oh_unemp_rate_2016 = 2.8

        contract = self._createContract(employee, salary, external_wages=external_wages,
                                        struct_id=self.ref('l10n_us_oh_hr_payroll.hr_payroll_salary_structure_us_oh_employee'))
        ## tax maximums
        OH_UNEMP_MAX_WAGE = 9000.0

        ## tax rates
        OH_UNEMP = contract.oh_unemp_rate(2016) / -100.0

        self._log('2016 Ohio_external tax first payslip:')
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['OH_UNEMP_WAGES'], OH_UNEMP_MAX_WAGE - external_wages)
        self.assertPayrollEqual(cats['OH_UNEMP'], cats['OH_UNEMP_WAGES'] * OH_UNEMP)


    def test_2016_taxes_with_state_exempt(self):
        salary = 5000.0
        external_wages = 6000.0

        employee = self._createEmployee()
        employee.company_id.oh_unemp_rate_2016 = 2.9

        contract = self._createContract(employee, salary, external_wages=external_wages, struct_id=self.ref(
            'l10n_us_oh_hr_payroll.hr_payroll_salary_structure_us_oh_employee'), futa_type=USHrContract.FUTA_TYPE_BASIC)
        ## tax maximums
        OH_UNEMP_MAX_WAGE = 9000.0

        ## tax rates
        OH_UNEMP = contract.oh_unemp_rate(2016) / -100.0

        self.assertPayrollEqual(OH_UNEMP, 0.0)

        self._log('2016 Ohio exempt tax first payslip:')
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['OH_UNEMP_WAGES'], OH_UNEMP_MAX_WAGE - external_wages)
        self.assertPayrollEqual(cats['OH_UNEMP'], cats['OH_UNEMP_WAGES'] * OH_UNEMP)