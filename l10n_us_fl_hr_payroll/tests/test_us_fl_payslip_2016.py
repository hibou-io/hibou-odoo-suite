# -*- coding: utf-8 -*-

from openerp.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip
from openerp.addons.l10n_us_hr_payroll.models.l10n_us_hr_payroll import USHrContract


class TestUsFlPayslip(TestUsPayslip):
    ###
    #   2016 Taxes and Rates
    ###

    def test_2016_taxes(self):
        salary = 5000.0;

        ## tax maximums
        FL_UNEMP_MAX_WAGE = 7000.0


        employee = self._createEmployee()
        employee.company_id.fl_unemp_rate_2016 = 2.7

        contract = self._createContract(employee, salary, struct_id=self.ref('l10n_us_fl_hr_payroll.hr_payroll_salary_structure_us_fl_employee'))

        ## tax rates
        FL_UNEMP = contract.fl_unemp_rate(2016) / -100.0

        self._log('2016 Florida tax first payslip:')
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FL_UNEMP_WAGES'], salary)
        self.assertPayrollEqual(cats['FL_UNEMP'], cats['FL_UNEMP_WAGES'] * FL_UNEMP)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_fl_unemp_wages = FL_UNEMP_MAX_WAGE - salary if (FL_UNEMP_MAX_WAGE - 2*salary < salary) else salary

        self._log('2016 Florida tax second payslip:')
        payslip = self._createPayslip(employee, '2016-02-01', '2016-02-29')  # 2016 is a leap year

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FL_UNEMP_WAGES'], remaining_fl_unemp_wages)
        self.assertPayrollEqual(cats['FL_UNEMP'], remaining_fl_unemp_wages * FL_UNEMP)


    def test_2016_taxes_with_external(self):
        salary = 5000.0;
        external_wages = 6000.0

        employee = self._createEmployee()
        employee.company_id.fl_unemp_rate_2016 = 2.7

        contract = self._createContract(employee, salary, external_wages=external_wages, struct_id=self.ref('l10n_us_fl_hr_payroll.hr_payroll_salary_structure_us_fl_employee'))
        ## tax maximums
        FL_UNEMP_MAX_WAGE = 7000.0

        ## tax rates
        FL_UNEMP = contract.fl_unemp_rate(2016) / -100.0

        self._log('2016 Forida_external tax first payslip:')
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FL_UNEMP_WAGES'], FL_UNEMP_MAX_WAGE - external_wages)
        self.assertPayrollEqual(cats['FL_UNEMP'], cats['FL_UNEMP_WAGES'] * FL_UNEMP)


    def test_2016_taxes_with_state_exempt(self):
        salary = 5000.0;
        external_wages = 6000.0

        employee = self._createEmployee()
        employee.company_id.fl_unemp_rate_2016 = 2.7

        contract = self._createContract(employee, salary, external_wages=external_wages, struct_id=self.ref(
            'l10n_us_fl_hr_payroll.hr_payroll_salary_structure_us_fl_employee'), futa_type=USHrContract.FUTA_TYPE_BASIC)
        ## tax maximums
        FL_UNEMP_MAX_WAGE = 7000.0

        ## tax rates
        FL_UNEMP = contract.fl_unemp_rate(2016) / -100.0

        self.assertPayrollEqual(FL_UNEMP, 0.0)

        self._log('2016 Forida_external tax first payslip:')
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['FL_UNEMP_WAGES'], FL_UNEMP_MAX_WAGE - external_wages)
        self.assertPayrollEqual(cats['FL_UNEMP'], cats['FL_UNEMP_WAGES'] * FL_UNEMP)