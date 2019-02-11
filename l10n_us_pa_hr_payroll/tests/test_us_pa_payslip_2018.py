from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip


class TestUsPAPayslip(TestUsPayslip):
    ###
    #    Taxes and Rates
    ###
    PA_UNEMP_MAX_WAGE = 10000.0
    ER_PA_UNEMP = -3.6890 / 100.0
    EE_PA_UNEMP = -0.06 / 100.0
    PA_INC_WITHHOLD = 3.07

    def test_2018_taxes(self):
        salary = 4166.67
        wh = -127.92

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, struct_id=self.ref('l10n_us_pa_hr_payroll.hr_payroll_salary_structure_us_pa_employee'))

        self._log('2018 Pennsylvania tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')
        payslip.onchange_contract()
        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_ER_US_PA_UNEMP'], salary)
        self.assertPayrollEqual(cats['EE_US_PA_UNEMP'], cats['BASIC'] * self.EE_PA_UNEMP)
        self.assertPayrollEqual(cats['ER_US_PA_UNEMP'], cats['WAGE_ER_US_PA_UNEMP'] * self.ER_PA_UNEMP)
        self.assertPayrollEqual(cats['EE_US_PA_INC_WITHHOLD'], wh)
