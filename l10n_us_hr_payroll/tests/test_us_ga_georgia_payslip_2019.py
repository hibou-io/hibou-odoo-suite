# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip


class TestUsGAPayslip(TestUsPayslip):

    # TAXES AND RATES
    GA_UNEMP_MAX_WAGE = 9500.00
    GA_UNEMP = -(2.70 / 100.0)

    def test_taxes_weekly_single_with_additional_wh(self):
        salary = 15000.00
        schedule_pay = 'weekly'
        allowances = 1
        filing_status = 'single'
        additional_wh = 12.50
        # Hand Calculated Amount to Test
        # Step 1 - Subtract standard deduction from wages. Std Deduct for single weekly is 88.50
        # step1 = 15000.00 - 88.50 = 14911.5
        # Step 2 - Subtract personal allowance from step1. Allowance for single weekly is 51.92
        # step2 = step1 - 51.92 = 14859.58
        # Step 3 - Subtract amount for dependents. Weekly dependent allowance is 57.50
        # step3 = 14859.58 - 57.50 = 14802.08
        # Step 4 -Determine wh amount from tables
        # step4 = 4.42 + ((5.75 / 100.00) * (14802.08 - 135.00))
        # Add additional_wh
        # wh = 847.7771 + 12.50 = 860.2771
        wh = -860.28

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('GA'),
                                        ga_g4_sit_dependent_allowances=allowances,
                                        ga_g4_sit_additional_allowances=0,
                                        ga_g4_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional_wh,
                                        schedule_pay=schedule_pay)

        self.assertEqual(contract.schedule_pay, 'weekly')

        self._log('2019 Georgia tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], self.GA_UNEMP_MAX_WAGE * self.GA_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)

        remaining_GA_UNEMP_wages = 0.0  # We already reached max unemployment wages.

        self._log('2019 Georgia tax second payslip weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_GA_UNEMP_wages * self.GA_UNEMP)


    def test_taxes_monthly_head_of_household(self):
        salary = 25000.00
        schedule_pay = 'monthly'
        allowances = 2
        filing_status = 'head of household'
        additional_wh = 15.00
        # Hand Calculated Amount to Test
        # Step 1 - Subtract standard deduction from wages. Std Deduct for head of household monthly is 383.50
        # step1 = 25000.00 - 383.50 = 24616.5
        # Step 2 - Subtract personal allowance from step1. Allowance for head of household monthly is 225.00
        # step2 = 24616.5 - 225.00 = 24391.5
        # Step 3 - Subtract amount for dependents. Weekly dependent allowance is 250.00
        # step3 = 24391.5 - (2 * 250.00) = 23891.5
        # Step 4 - Determine wh amount from tables
        # step4 = 28.33 + ((5.75 / 100.00) * (23891.5 - 833.00)) = 1354.19375
        # Add additional_wh
        # wh = 1354.19375 + 15.00 = 1369.19375
        wh = -1369.19

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('GA'),
                                        ga_g4_sit_dependent_allowances=allowances,
                                        ga_g4_sit_additional_allowances=0,
                                        ga_g4_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional_wh,
                                        schedule_pay=schedule_pay)

        self.assertEqual(contract.schedule_pay, 'monthly')

        self._log('2019 Georgia tax first payslip monthly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], self.GA_UNEMP_MAX_WAGE * self.GA_UNEMP)
        self.assertPayrollAlmostEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)

        remaining_GA_UNEMP_wages = 0.0  # We already reached max unemployment wages.

        self._log('2019 Georgia tax second payslip weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_GA_UNEMP_wages * self.GA_UNEMP)

    def test_taxes_exempt(self):
        salary = 25000.00
        schedule_pay = 'monthly'
        allowances = 2
        filing_status = ''
        additional_wh = 15.00

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('GA'),
                                        ga_g4_sit_dependent_allowances=allowances,
                                        ga_g4_sit_additional_allowances=0,
                                        ga_g4_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional_wh,
                                        schedule_pay=schedule_pay)

        self._log('2019 Georgia tax first payslip exempt:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats.get('EE_US_SIT', 0), 0)
