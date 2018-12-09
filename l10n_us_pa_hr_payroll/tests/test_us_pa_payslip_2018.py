from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip
from odoo.addons.l10n_us_hr_payroll.l10n_us_hr_payroll import USHrContract


class TestUsPAPayslip(TestUsPayslip):
    ###
    #    Taxes and Rates
    ###
    PA_UNEMP_MAX_WAGE = 10000.0

    def test_2018_taxes(self):
        self.debug = True
        salary = 4166.67
        wh = -127.92

        employee = self._createEmployee()
        employee.company_id.pa_unemp_employee_rate_2018 = 0.06
        employee.company_id.pa_unemp_company_rate_2018 = 3.6785
        employee.company_id.pa_withhold_rate_2018 = 3.07

        contract = self._createContract(employee, salary, struct_id=self.ref('l10n_us_pa_hr_payroll.hr_payroll_salary_structure_us_pa_employee'))

        # tax rates
        pa_unemp_employee = contract.pa_unemp_employee_rate(2018) / -100.0
        pa_unemp_company = contract.pa_unemp_company_rate(2018) / -100.0


        self._log('2018 Pennsylvania tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')
        payslip.onchange_contract()
        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['PA_UNEMP_WAGES'], salary)
        self.assertPayrollEqual(cats['PA_UNEMP_EMPLOYEE'], cats['PA_UNEMP_WAGES'] * pa_unemp_employee)
        self.assertPayrollEqual(cats['PA_UNEMP_COMPANY'], cats['PA_UNEMP_WAGES'] * pa_unemp_company)
        self.assertPayrollEqual(cats['PA_WITHHOLD'], wh)

