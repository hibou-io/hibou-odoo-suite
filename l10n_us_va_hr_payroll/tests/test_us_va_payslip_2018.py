# -*- coding: utf-8 -*-

from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip
from odoo.addons.l10n_us_hr_payroll.l10n_us_hr_payroll import USHrContract


class TestUsVaPayslip(TestUsPayslip):
    ###
    #    Taxes and Rates
    ###
    VA_UNEMP_MAX_WAGE = 8000.0

    def test_2018_taxes(self):
        salary = 5000.0

        # For formula from https://www.tax.virginia.gov/withholding-calculator
        """
        Key
        G = Gross Pay for Pay Period	P = Pay periods per year
        A = Annualized gross pay	E1 = Personal and Dependent Exemptions
        T = Annualized taxable income	E2 = Age 65 and Over & Blind Exemptions
        WH = Tax to be withheld for pay period	W = Annualized tax to be withheld
        G x P - [$3000+ (E1 x 930) + (E2 x 800)] = T
        Calculate W as follows:
        If T is:	W is:
        Not over $3,000	2% of T
        Over	But Not Over	Then
        $3,000	$5,000	        $60 + (3% of excess over $3,000)
        $5,000	$17,000	        $120 + (5% of excess over $5,000)
        $17,000	 	            $720 + (5.75% of excess over $17,000)
        W / P = WH
        """
        e1 = 2
        e2 = 0
        t = salary * 12 - (3000 + (e1 * 930) + (e2 * 800))

        if t <= 3000:
            w = 0.02 * t
        elif t <= 5000:
            w = 60 + (0.03 * (t - 3000))
        elif t <= 17000:
            w = 120 + (0.05 * (t - 5000))
        else:
            w = 720 + (0.0575 * (t - 17000))

        wh = w / 12

        employee = self._createEmployee()
        employee.company_id.va_unemp_rate_2018 = 2.53

        contract = self._createContract(employee, salary, struct_id=self.ref('l10n_us_va_hr_payroll.hr_payroll_salary_structure_us_va_employee'))
        contract.va_va4_exemptions = e1
        contract.va_va4p_exemptions = e2

        # tax rates
        va_unemp = contract.va_unemp_rate(2018) / -100.0

        self._log('2017 Virginia tax last payslip:')
        payslip = self._createPayslip(employee, '2017-12-01', '2017-12-31')
        payslip.compute_sheet()
        process_payslip(payslip)

        self._log('2018 Virginia tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['VA_UNEMP_WAGES'], salary)
        self.assertPayrollEqual(cats['VA_UNEMP'], cats['VA_UNEMP_WAGES'] * va_unemp)
        self.assertPayrollEqual(cats['VA_INC_WITHHOLD'], -wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_va_unemp_wages = self.VA_UNEMP_MAX_WAGE - salary if (self.VA_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2018 Virginia tax second payslip:')
        payslip = self._createPayslip(employee, '2018-02-01', '2018-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['VA_UNEMP_WAGES'], remaining_va_unemp_wages)
        self.assertPayrollEqual(cats['VA_UNEMP'], remaining_va_unemp_wages * va_unemp)

    def test_2018_taxes_with_external(self):
        salary = 5000.0
        external_wages = 6000.0

        employee = self._createEmployee()
        employee.company_id.va_unemp_rate_2018 = 2.8

        contract = self._createContract(employee, salary, external_wages=external_wages,
                                        struct_id=self.ref('l10n_us_va_hr_payroll.hr_payroll_salary_structure_us_va_employee'))

        # tax rates
        va_unemp = contract.va_unemp_rate(2018) / -100.0

        self._log('2018 Virginia_external tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['VA_UNEMP_WAGES'], self.VA_UNEMP_MAX_WAGE - external_wages)
        self.assertPayrollEqual(cats['VA_UNEMP'], cats['VA_UNEMP_WAGES'] * va_unemp)

    def test_2018_taxes_with_state_exempt(self):
        salary = 5000.0
        external_wages = 6000.0

        employee = self._createEmployee()
        employee.company_id.va_unemp_rate_2018 = 2.9

        contract = self._createContract(employee, salary, external_wages=external_wages, struct_id=self.ref(
            'l10n_us_va_hr_payroll.hr_payroll_salary_structure_us_va_employee'), futa_type=USHrContract.FUTA_TYPE_BASIC)

        # tax rates
        va_unemp = contract.va_unemp_rate(2018) / -100.0

        self.assertPayrollEqual(va_unemp, 0.0)

        self._log('2018 Virginia exempt tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['VA_UNEMP_WAGES'], self.VA_UNEMP_MAX_WAGE - external_wages)
        self.assertPayrollEqual(cats['VA_UNEMP'], cats['VA_UNEMP_WAGES'] * va_unemp)
