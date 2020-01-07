# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip


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
        contract = self._createContract(employee,
                                        wage=wages,
                                        state_id=self.get_us_state('IA'),
                                        state_income_tax_additional_withholding=additional_wh,
                                        ia_w4_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)

        self._log('2019 Iowa tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        # T1 is the gross taxable wages for the pay period minus the Federal withholding amount. We add the federal
        # withholding amount because it is calculated in the base US payroll module as a negative
        # t1 = 30000 - (10399.66) = 19600.34
        t1_to_test = wages + cats['EE_US_941_FIT']
        self.assertPayrollAlmostEqual(t1_to_test, 19600.34)

        # T2 is T1 minus our standard deduction which is a table of flat rates dependent on the number of allowances.
        # In our case, we have a weekly period which on the table has a std deduct. of $32.50 for 0 or 1 allowances,
        # and 80.00 of 2 or more allowances.
        standard_deduction = 32.50  # The allowance tells us what standard_deduction amount to use.
        # t2 = 19600.34 - 32.50 = 19567.84
        t2_to_test = t1_to_test - standard_deduction
        self.assertPayrollAlmostEqual(t2_to_test, 19567.84)
        # T3 is T2 multiplied by the income rates in the large table plus a flat fee for that bracket.
        # 1153.38 is the bracket floor. 8.53 is the rate, and 67.63 is the flat fee.
        # t3 = 1638.38
        t3_to_test = ((t2_to_test - 1153.38) * (8.53 / 100)) + 67.63
        self.assertPayrollAlmostEqual(t3_to_test, 1638.38)
        # T4 is T3 minus a flat amount determined by pay period * the number of deductions. For 2019, our weekly
        # deduction amount per allowance is 0.77
        # t4 = 1638.38 - 0.77 = 155.03
        t4_to_test = t3_to_test - (0.77 * allowances)
        self.assertPayrollAlmostEqual(t4_to_test, 1637.61)
        # t5 is our T4 plus the additional withholding per period
        # t5 = 1637.61 + 0.0
        # Convert to negative as well.
        t5_to_test = -t4_to_test - additional_wh
        self.assertPayrollAlmostEqual(t5_to_test, -1637.61)

        self.assertPayrollEqual(cats['ER_US_SUTA'], wages * self.IA_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], t5_to_test)


        # Make a new payslip, this one will have maximums

        remaining_IA_UNEMP_wages = self.IA_UNEMP_MAX_WAGE - wages if (self.IA_UNEMP_MAX_WAGE - 2*wages < wages) \
            else wages

        self._log('2019 Iowa tax second payslip weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], wages * self.IA_UNEMP)

    def test_taxes_biweekly(self):
        wages = 3000.00
        schedule_pay = 'bi-weekly'
        allowances = 1
        additional_wh = 0.00
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wages,
                                        state_id=self.get_us_state('IA'),
                                        state_income_tax_additional_withholding=additional_wh,
                                        ia_w4_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)

        self._log('2019 Iowa tax first payslip bi-weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        # T1 is the gross taxable wages for the pay period minus the Federal withholding amount. We add the federal
        # withholding amount because it is calculated in the base US payroll module as a negative
        t1_to_test = wages + cats['EE_US_941_FIT']
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

        self.assertPayrollEqual(cats['ER_US_SUTA'], wages * self.IA_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], t5_to_test - additional_wh)

        process_payslip(payslip)

    def test_taxes_with_external_weekly(self):
        wages = 2500.00
        schedule_pay = 'weekly'
        allowances = 1
        additional_wh = 0.00

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wages,
                                        state_id=self.get_us_state('IA'),
                                        state_income_tax_additional_withholding=additional_wh,
                                        ia_w4_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)

        self._log('2019 Iowa external tax first payslip external weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)


        # T1 is the gross taxable wages for the pay period minus the Federal withholding amount. We add the federal
        # withholding amount because it is calculated in the base US payroll module as a negative
        t1_to_test = wages + cats['EE_US_941_FIT']
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

        self.assertPayrollEqual(cats['ER_US_SUTA'], wages * self.IA_UNEMP)
        self.assertPayrollAlmostEqual(cats['EE_US_SIT'], t5_to_test)

        process_payslip(payslip)