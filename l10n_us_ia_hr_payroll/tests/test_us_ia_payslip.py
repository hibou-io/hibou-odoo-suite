from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip
from odoo.addons.l10n_us_hr_payroll.models.l10n_us_hr_payroll import USHrContract


class TestUsIAPayslip(TestUsPayslip):
    IA_UNEMP_MAX_WAGE = 30600
    IA_UNEMP = -1.0 / 100.0
    IA_INC_TAX = -0.0535

    def test_taxes_weekly(self):
        wages = 30000.00
        schedule_pay = 'weekly'
        allowances = 1
        additional_wh = 0.00
        employee = self._createEmployee()
        contract = self._createContract(employee, wages,
                                        struct_id=self.ref('l10n_us_ia_hr_payroll.hr_payroll_salary_structure_us_ia_employee'),
                                        schedule_pay=schedule_pay)
        contract.ia_w4_allowances = allowances
        contract.ia_w4_additional_wh = additional_wh

        self.assertEqual(contract.schedule_pay, 'weekly')

        self._log('2019 Iowa tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        # T1 is the gross taxable wages for the pay period minus the Federal withholding amount. We add the federal
        # withholding amount because it is calculated in the base US payroll module as a negative
        # t1 = 30000 - (10399.66) = 19600.34
        t1_to_test = wages + cats['EE_US_FED_INC_WITHHOLD']
        self.assertPayrollEqual(t1_to_test, 19600.34)

        # T2 is T1 minus our standard deduction which is a table of flat rates dependent on the number of allowances.
        # In our case, we have a weekly period which on the table has a std deduct. of $32.50 for 0 or 1 allowances,
        # and 80.00 of 2 or more allowances.
        standard_deduction = 32.50  # The allowance tells us what standard_deduction amount to use.
        # t2 = 19600.34 - 32.50 = 19567.84
        t2_to_test = t1_to_test - standard_deduction
        self.assertPayrollEqual(t2_to_test, 19567.84)
        # T3 is T2 multiplied by the income rates in the large table plus a flat fee for that bracket.
        # 1153.38 is the bracket floor. 8.53 is the rate, and 67.63 is the flat fee.
        # t3 = 1638.38
        t3_to_test = ((t2_to_test - 1153.38) * (8.53 / 100)) + 67.63
        self.assertPayrollEqual(t3_to_test, 1638.38)
        # T4 is T3 minus a flat amount determined by pay period * the number of deductions. For 2019, our weekly
        # deduction amount per allowance is 0.77
        # t4 = 1638.38 - 0.77 = 155.03
        t4_to_test = t3_to_test - (0.77 * allowances)
        self.assertPayrollEqual(t4_to_test, 1637.61)
        # t5 is our T4 plus the additional withholding per period
        # t5 = 1637.61 + 0.0
        # Convert to negative as well.
        t5_to_test = -t4_to_test - additional_wh
        self.assertPayrollEqual(t5_to_test, -1637.61)

        self.assertPayrollEqual(cats['WAGE_US_IA_UNEMP'], wages)
        self.assertPayrollEqual(cats['ER_US_IA_UNEMP'], cats['WAGE_US_IA_UNEMP'] * self.IA_UNEMP)
        self.assertPayrollEqual(cats['EE_US_IA_INC_WITHHOLD'], t5_to_test)

        # Test additional
        additional_wh = 15.00
        contract.ia_w4_additional_wh = additional_wh
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats['EE_US_IA_INC_WITHHOLD'], t5_to_test - additional_wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_IA_UNEMP_wages = self.IA_UNEMP_MAX_WAGE - wages if (self.IA_UNEMP_MAX_WAGE - 2*wages < wages) \
            else wages

        self._log('2019 Iowa tax second payslip weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_IA_UNEMP'], remaining_IA_UNEMP_wages)
        self.assertPayrollEqual(cats['ER_US_IA_UNEMP'], remaining_IA_UNEMP_wages * self.IA_UNEMP)

    def test_taxes_biweekly(self):
        wages = 3000.00
        schedule_pay = 'bi-weekly'
        allowances = 1
        additional_wh = 0.00
        employee = self._createEmployee()
        contract = self._createContract(employee, wages,
                                        struct_id=self.ref(
                                            'l10n_us_ia_hr_payroll.hr_payroll_salary_structure_us_ia_employee'),
                                        schedule_pay=schedule_pay)
        contract.ia_w4_allowances = allowances
        contract.ia_w4_additional_wh = additional_wh

        self.assertEqual(contract.schedule_pay, 'bi-weekly')

        self._log('2019 Iowa tax first payslip bi-weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        # T1 is the gross taxable wages for the pay period minus the Federal withholding amount. We add the federal
        # withholding amount because it is calculated in the base US payroll module as a negative
        t1_to_test = wages + cats['EE_US_FED_INC_WITHHOLD']
        # T2 is T1 minus our standard deduction which is a table of flat rates dependent on the number of allowances.
        # In our case, we have a biweekly period which on the table has a std deduct. of $65.00 for 0 or 1 allowances,
        # and $160.00 of 2 or more allowances.
        standard_deduction = 65.00  # The allowance tells us what standard_deduction amount to use.
        t2_to_test = t1_to_test - standard_deduction
        # T3 is T2 multiplied by the income rates in the large table plus a flat fee for that bracket.
        t3_to_test = ((t2_to_test - 2306.77) * (8.53 / 100)) + 135.28
        # T4 is T3 minus a flat amount determined by pay period * the number of deductions. For 2019, our weekly
        # deduction amount per allowance is 0.77
        t4_to_test = t3_to_test - (1.54 * allowances)
        # t5 is our T4 plus the additional withholding per period
        t5_to_test = -t4_to_test - additional_wh

        self.assertPayrollEqual(cats['WAGE_US_IA_UNEMP'], wages)
        self.assertPayrollEqual(cats['ER_US_IA_UNEMP'], cats['WAGE_US_IA_UNEMP'] * self.IA_UNEMP)
        self.assertPayrollEqual(cats['EE_US_IA_INC_WITHHOLD'], t5_to_test - additional_wh)

        process_payslip(payslip)

    def test_taxes_with_external_weekly(self):
        wages = 2500.00
        schedule_pay = 'weekly'
        allowances = 1
        additional_wh = 0.00
        external_wages = 500.0

        employee = self._createEmployee()
        contract = self._createContract(employee, wages, external_wages=external_wages,
                                        struct_id=self.ref('l10n_us_ia_hr_payroll.hr_payroll_salary_structure_us_ia_employee'),
                                        schedule_pay=schedule_pay)
        contract.ia_w4_additional_wh = additional_wh
        contract.ia_w4_allowances = allowances

        self._log('2019 Iowa external tax first payslip external weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)


        # T1 is the gross taxable wages for the pay period minus the Federal withholding amount. We add the federal
        # withholding amount because it is calculated in the base US payroll module as a negative
        t1_to_test = wages + cats['EE_US_FED_INC_WITHHOLD']
        # T2 is T1 minus our standard deduction which is a table of flat rates dependent on the number of allowances.
        # In our case, we have a weekly period which on the table has a std deduct. of $32.50 for 0 or 1 allowances,
        # and 80.00 of 2 or more allowances.
        standard_deduction = 32.50  # The allowance tells us what standard_deduction amount to use.
        t2_to_test = t1_to_test - standard_deduction
        # T3 is T2 multiplied by the income rates in the large table plus a flat fee for that bracket.
        t3_to_test = ((t2_to_test - 1153.38) * (8.53 / 100)) + 67.63
        # T4 is T3 minus a flat amount determined by pay period * the number of deductions. For 2019, our weekly
        # deduction amount per allowance is 0.77
        t4_to_test = t3_to_test - (0.77 * allowances)
        # t5 is our T4 plus the additional withholding per period
        t5_to_test = -t4_to_test - additional_wh

        self.assertPayrollEqual(cats['WAGE_US_IA_UNEMP'], wages)
        self.assertPayrollEqual(cats['ER_US_IA_UNEMP'], cats['WAGE_US_IA_UNEMP'] * self.IA_UNEMP)
        self.assertPayrollEqual(cats['EE_US_IA_INC_WITHHOLD'], t5_to_test)

        process_payslip(payslip)

    def test_taxes_with_state_exempt_weekly(self):
        salary = 5000.0
        external_wages = 10000.0
        schedule_pay = 'weekly'

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        salary,
                                        external_wages=external_wages,
                                        struct_id=self.ref('l10n_us_ia_hr_payroll.hr_payroll_salary_structure_us_ia_employee'),
                                        futa_type=USHrContract.FUTA_TYPE_BASIC,
                                        schedule_pay=schedule_pay)
        contract.ia_w4_tax_exempt = True

        self._log('2019 Iowa exempt tax first payslip exempt weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats.get('WAGE_US_IA_UNEMP', 0.0), 0.0)
        self.assertPayrollEqual(cats.get('ER_US_IA_UNEMP', 0.0), cats.get('WAGE_US_IA_UNEMP', 0.0) * self.IA_UNEMP)




