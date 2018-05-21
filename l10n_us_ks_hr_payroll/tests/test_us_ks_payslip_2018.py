from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip
from odoo.addons.l10n_us_hr_payroll.l10n_us_hr_payroll import USHrContract


class TestUsKSPayslip(TestUsPayslip):
    ###
    #   2018 Taxes and Rates
    ###
    KS_UNEMP_MAX_WAGE = 14000.0

    def test_2018_taxes(self):
        self.debug = True
        salary = 210
        schedule_pay = 'weekly'
        allowances = 2
        additional_withholding = 0

        # Amount of each withholding allowance for weekly from Withholding Allowance Amounts Table
        # https://www.ksrevenue.org/pdf/kw1002017.pdf
        withholding_allowance = 43.27 * allowances
        taxable_pay = salary - withholding_allowance

        # Tax Percentage Method for Single, taxable pay over $58, under $346
        wh = -round(((taxable_pay - 58) * 0.031) - additional_withholding, 2)

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref(
                                            'l10n_us_ks_hr_payroll.hr_payroll_salary_structure_us_ks_employee'),
                                        schedule_pay=schedule_pay)
        contract.ks_k4_allowances = allowances
        contract.ks_additional_withholding = additional_withholding
        contract.ks_k4_filing_status = 'single'

        self.assertEqual(contract.schedule_pay, 'weekly')

        # tax rates
        ks_unemp = contract.ks_unemp_rate(2018) / -100.0

        self._log('2018 Kansas tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['KS_UNEMP_WAGES'], salary)
        self.assertPayrollEqual(cats['KS_UNEMP'], cats['KS_UNEMP_WAGES'] * ks_unemp)
        self.assertPayrollEqual(cats['KS_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_ks_unemp_wages = self.KS_UNEMP_MAX_WAGE - salary if (self.KS_UNEMP_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2018 Kansas tax second payslip:')
        payslip = self._createPayslip(employee, '2018-02-01', '2018-02-28')
        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['KS_UNEMP_WAGES'], remaining_ks_unemp_wages)
        self.assertPayrollEqual(cats['KS_UNEMP'], remaining_ks_unemp_wages * ks_unemp)

    def test_2018_taxes_with_state_exempt(self):
        salary = 210
        schedule_pay = 'weekly'
        allowances = 2

        # Tax Exempt
        wh = 0

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref(
                                            'l10n_us_ks_hr_payroll.hr_payroll_salary_structure_us_ks_employee'),
                                        schedule_pay=schedule_pay)
        contract.ks_k4_allowances = allowances
        contract.ks_k4_filing_status = 'exempt'

        payslip = self._createPayslip(employee, '2018-02-01', '2018-02-28')
        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertEqual(cats['KS_WITHHOLD'], wh)
