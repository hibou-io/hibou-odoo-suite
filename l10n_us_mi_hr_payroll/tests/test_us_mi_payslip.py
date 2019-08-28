from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip
from odoo.addons.l10n_us_hr_payroll.models.l10n_us_hr_payroll import USHrContract


class TestUsMIPayslip(TestUsPayslip):

    # Taxes and Rates
    MI_UNEMP_MAX_WAGE = 9000.0
    MI_UNEMP = - 6.0 / 100.0
    MI_INC_TAX = - 4.25 / 100.0
    ANNUAL_EXEMPTION_AMOUNT = 4400.00
    PAY_PERIOD_DIVISOR = {
        'weekly': 52.0,
        'bi-weekly': 26.0,
        'semi-monthly': 24.0,
        'monthly': 12.0
    }

    def test_2019_taxes_weekly(self):
        salary = 5000.0
        schedule_pay = 'weekly'
        exemptions = 1
        allowance_amount = self.ANNUAL_EXEMPTION_AMOUNT / self.PAY_PERIOD_DIVISOR[schedule_pay]
        wh = -((salary - (allowance_amount * exemptions)) * -self.MI_INC_TAX)

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref('l10n_us_mi_hr_payroll.hr_payroll_salary_structure_us_mi_employee'),
                                        schedule_pay=schedule_pay)
        contract.mi_w4_exemptions = exemptions

        self.assertEqual(contract.schedule_pay, 'weekly')

        self._log('2019 Michigan tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_MI_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_MI_UNEMP'], cats['WAGE_US_MI_UNEMP'] * self.MI_UNEMP)
        self.assertPayrollEqual(cats['EE_US_MI_INC_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums
        remaining_MI_UNEMP_wages = self.MI_UNEMP_MAX_WAGE - salary if (self.MI_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2019 Michigan tax second payslip weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_MI_UNEMP'], remaining_MI_UNEMP_wages)
        self.assertPayrollEqual(cats['ER_US_MI_UNEMP'], remaining_MI_UNEMP_wages * self.MI_UNEMP)

    def test_2019_taxes_with_external_weekly(self):
        salary = 5000.0
        external_wages = 30000.0
        schedule_pay = 'weekly'

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        salary,
                                        external_wages=external_wages,
                                        struct_id=self.ref('l10n_us_mi_hr_payroll.hr_payroll_salary_structure_us_mi_employee'),
                                        schedule_pay=schedule_pay)

        self._log('2019 Michigan external tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_MI_UNEMP'], max(self.MI_UNEMP_MAX_WAGE - external_wages, 0.0))
        self.assertPayrollEqual(cats['ER_US_MI_UNEMP'], cats['WAGE_US_MI_UNEMP'] * self.MI_UNEMP)

    def test_2019_taxes_with_state_exempt_weekly(self):
        salary = 5000.0
        external_wages = 10000.0
        schedule_pay = 'weekly'

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, external_wages=external_wages, struct_id=self.ref(
                                        'l10n_us_mi_hr_payroll.hr_payroll_salary_structure_us_mi_employee'),
                                        futa_type=USHrContract.FUTA_TYPE_BASIC, schedule_pay=schedule_pay)

        self._log('2019 Michigan exempt tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats.get('WAGE_US_MI_UNEMP', 0.0), 0.0)
        self.assertPayrollEqual(cats.get('ER_US_MI_UNEMP', 0.0), cats.get('WAGE_US_MI_UNEMP', 0.0) * self.MI_UNEMP)

    def test_2019_taxes_biweekly(self):
        salary = 5000.0
        schedule_pay = 'bi-weekly'
        allowance_amount = 0.0
        allowance_amount = self.ANNUAL_EXEMPTION_AMOUNT / self.PAY_PERIOD_DIVISOR[schedule_pay]
        allowances = 2

        wh = -((salary - (allowance_amount * allowances)) * -self.MI_INC_TAX)

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, struct_id=self.ref(
                                        'l10n_us_mi_hr_payroll.hr_payroll_salary_structure_us_mi_employee'),
                                        schedule_pay=schedule_pay)
        contract.mi_w4_exemptions = allowances

        self.assertEqual(contract.schedule_pay, 'bi-weekly')

        self._log('2019 Michigan tax first payslip bi-weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_MI_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_MI_UNEMP'], cats['WAGE_US_MI_UNEMP'] * self.MI_UNEMP)
        self.assertPayrollEqual(cats['EE_US_MI_INC_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums
        remaining_MI_UNEMP_wages = self.MI_UNEMP_MAX_WAGE - salary if (self.MI_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2019 Michigan tax second payslip bi-weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_MI_UNEMP'], remaining_MI_UNEMP_wages)
        self.assertPayrollEqual(cats['ER_US_MI_UNEMP'], remaining_MI_UNEMP_wages * self.MI_UNEMP)

    def test_2019_taxes_semimonthly(self):
        salary = 5000.0
        schedule_pay = 'semi-monthly'
        allowance_amount = self.ANNUAL_EXEMPTION_AMOUNT / self.PAY_PERIOD_DIVISOR[schedule_pay]
        allowances = 1

        wh = -((salary - (allowance_amount * allowances)) * -self.MI_INC_TAX)

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, struct_id=self.ref(
                                        'l10n_us_mi_hr_payroll.hr_payroll_salary_structure_us_mi_employee'),
                                        schedule_pay=schedule_pay)
        contract.mi_w4_exemptions = allowances

        self.assertEqual(contract.schedule_pay, 'semi-monthly')

        self._log('2019 Michigan tax first payslip semi-monthly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_MI_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_MI_UNEMP'], cats['WAGE_US_MI_UNEMP'] * self.MI_UNEMP)
        self.assertPayrollEqual(cats['EE_US_MI_INC_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums
        remaining_MI_UNEMP_wages = self.MI_UNEMP_MAX_WAGE - salary if (self.MI_UNEMP_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2019 Michigan tax second payslip semi-monthly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_MI_UNEMP'], remaining_MI_UNEMP_wages)
        self.assertPayrollEqual(cats['ER_US_MI_UNEMP'], remaining_MI_UNEMP_wages * self.MI_UNEMP)

    def test_2019_taxes_monthly(self):
        salary = 5000.0
        schedule_pay = 'monthly'
        allowance_amount = self.ANNUAL_EXEMPTION_AMOUNT / self.PAY_PERIOD_DIVISOR[schedule_pay]
        allowances = 1

        wh = -((salary - (allowance_amount * allowances)) * -self.MI_INC_TAX)

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, struct_id=self.ref(
                                        'l10n_us_mi_hr_payroll.hr_payroll_salary_structure_us_mi_employee'),
                                        schedule_pay=schedule_pay)
        contract.mi_w4_exemptions = allowances

        self.assertEqual(contract.schedule_pay, 'monthly')

        self._log('2019 Michigan tax first payslip monthly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_MI_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_MI_UNEMP'], cats['WAGE_US_MI_UNEMP'] * self.MI_UNEMP)
        self.assertPayrollEqual(cats['EE_US_MI_INC_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums
        remaining_MI_UNEMP_wages = self.MI_UNEMP_MAX_WAGE - salary if (
                    self.MI_UNEMP_MAX_WAGE - (2 * salary) < salary) \
            else salary

        self._log('2019 Michigan tax second payslip monthly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_MI_UNEMP'], remaining_MI_UNEMP_wages)
        self.assertPayrollEqual(cats['ER_US_MI_UNEMP'], remaining_MI_UNEMP_wages * self.MI_UNEMP)

    def test_tax_exempt(self):
        salary = 5000.0
        wh = 0
        schedule_pay = 'weekly'
        exemptions = 1

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, struct_id=self.ref(
                                        'l10n_us_mi_hr_payroll.hr_payroll_salary_structure_us_mi_employee'),
                                        schedule_pay=schedule_pay)
        contract.mi_w4_exemptions = exemptions
        contract.mi_w4_tax_exempt = True

        self.assertEqual(contract.schedule_pay, 'weekly')

        self._log('2019 Michigan tax first payslip exempt:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_MI_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_MI_UNEMP'], cats['WAGE_US_MI_UNEMP'] * self.MI_UNEMP)
        self.assertPayrollEqual(cats.get('EE_US_MI_INC_WITHHOLD', 0.0), 0.0)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums
        remaining_MI_UNEMP_wages = self.MI_UNEMP_MAX_WAGE - salary if (
                    self.MI_UNEMP_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2019 Michigan tax second payslip exempt:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_MI_UNEMP'], remaining_MI_UNEMP_wages)
        self.assertPayrollEqual(cats['ER_US_MI_UNEMP'], remaining_MI_UNEMP_wages * self.MI_UNEMP)

    def test_additional_withholding(self):
        salary = 5000.0
        schedule_pay = 'weekly'
        allowance_amount = 0.0
        allowance_amount = self.ANNUAL_EXEMPTION_AMOUNT / self.PAY_PERIOD_DIVISOR[schedule_pay]
        additional_wh = 40.0
        allowances = 1

        wh = -(((salary - (allowance_amount * allowances)) * -self.MI_INC_TAX) + additional_wh)

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref('l10n_us_mi_hr_payroll.hr_payroll_salary_structure_us_mi_employee'),
                                        schedule_pay=schedule_pay)
        contract.mi_w4_additional_wh = additional_wh
        contract.mi_w4_exemptions = allowances

        self.assertEqual(contract.schedule_pay, 'weekly')

        self._log('2019 Michigan tax first payslip with additional withholding:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_MI_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_MI_UNEMP'], cats['WAGE_US_MI_UNEMP'] * self.MI_UNEMP)
        self.assertPayrollEqual(cats['EE_US_MI_INC_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums
        remaining_MI_UNEMP_wages = 4000.00

        self._log('2019 Michigan tax second payslip with additional withholding:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_MI_UNEMP'], remaining_MI_UNEMP_wages)
        self.assertPayrollEqual(cats['ER_US_MI_UNEMP'], remaining_MI_UNEMP_wages * self.MI_UNEMP)
