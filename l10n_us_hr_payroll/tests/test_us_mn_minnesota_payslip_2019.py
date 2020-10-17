# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip


class TestUsMNPayslip(TestUsPayslip):
    # TAXES AND RATES
    MN_UNEMP_MAX_WAGE = 34000.0
    MN_UNEMP = -1.11 / 100.0

    def test_taxes_weekly(self):
        salary = 30000.0
        # Hand Calculated Amount to Test
        # Step 1 -> 30000.00 for wages per period  Step 2 -> 52.0 for weekly -> 30000 * 52 -> 1560000
        # Step 3 -> allowances * 4250.0 -> 4250.00 in this case.
        # Step 4 -> Step 2 - Step 3  -> 1560000 - 4250.00 -> 1555750
        # Step 5 -> using chart -> we have last row -> ((1555750 - 166290) * (9.85 / 100)) + 11717.65 -> 148579.46
        # Step 6 -> Convert back to pay period amount and round - > 2857.297 - > 2857.0
        # wh = 2857.0
        wh = -2857.0

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MN'),
                                        mn_w4mn_sit_filing_status='single',
                                        state_income_tax_additional_withholding=0.0,
                                        mn_w4mn_sit_allowances=1.0,
                                        schedule_pay='weekly')

        self._log('2019 Minnesota tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.MN_UNEMP)
        self.assertPayrollAlmostEqual(cats['EE_US_SIT'], wh)  # Test numbers are off by 1 penny

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums
        remaining_MN_UNEMP_wages = self.MN_UNEMP_MAX_WAGE - salary if (self.MN_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2019 Minnesota tax second payslip weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_MN_UNEMP_wages * self.MN_UNEMP)

    def test_taxes_married(self):
        salary = 5000.00

        # Hand Calculated Amount to Test
        # Step 1 -> 5000.0 for wages per period  Step 2 -> 52.0 for weekly -> 5000 * 52 -> 260,000
        # Step 3 -> allowances * 4250.0 -> 4250.00 in this case.
        # Step 4 -> Step 2 - Step 3  -> 260,000 - 4250.00 -> 255750.0
        # For step five we used the married section
        # Step 5 -> using chart -> we have 2nd last row -> ((255750 - 163070) * (7.85 / 100)) + 10199.33 ->
        # Step 6 -> Convert back to pay period amount and round
        # wh = 336.0
        wh = -336.0

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MN'),
                                        mn_w4mn_sit_filing_status='married',
                                        state_income_tax_additional_withholding=0.0,
                                        mn_w4mn_sit_allowances=1.0,
                                        schedule_pay='weekly')

        self._log('2019 Minnesota tax first payslip married:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.MN_UNEMP)
        self.assertPayrollAlmostEqual(cats['EE_US_SIT'], wh)

    def test_taxes_semimonthly(self):
        salary = 6500.00
        # Hand Calculated Amount to Test
        # Step 1 -> 6500.00 for wages per period  Step 2 -> 24 for semi-monthly -> 6500.00 * 24 -> 156000.00
        # Step 3 -> allowances * 4250.0 -> 4250.00 in this case.
        # Step 4 -> Step 2 - Step 3  -> 156000.00 - 4250.00 -> 151750.0
        # Step 5 -> using chart -> we have 2nd last row -> ((151750.0- 89510) * (7.85 / 100)) + 5690.42 -> 10576.26
        # Step 6 -> Convert back to pay period amount and round
        # wh = -441
        wh = -441.00

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MN'),
                                        mn_w4mn_sit_filing_status='single',
                                        state_income_tax_additional_withholding=0.0,
                                        mn_w4mn_sit_allowances=1.0,
                                        schedule_pay='semi-monthly')


        self._log('2019 Minnesota tax first payslip semimonthly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.MN_UNEMP)
        self.assertPayrollAlmostEqual(cats['EE_US_SIT'], wh)

    def test_tax_exempt(self):
        salary = 5500.00
        wh = 0
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MN'),
                                        mn_w4mn_sit_filing_status='',
                                        state_income_tax_additional_withholding=0.0,
                                        mn_w4mn_sit_allowances=2.0,
                                        schedule_pay='weekly')

        self._log('2019 Minnesota tax first payslip exempt:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.MN_UNEMP)
        self.assertPayrollAlmostEqual(cats['EE_US_SIT'], wh)

    def test_additional_withholding(self):
        salary = 5500.0
        # Hand Calculated Amount to Test
        # Step 1 -> 5500 for wages per period  Step 2 -> 52 for weekly -> 5500 * 52 -> 286000.00
        # Step 3 -> allowances * 4250.0 -> 8500 in this case.
        # Step 4 -> Step 2 - Step 3  -> 286000.00 - 8500 -> 277500
        # Step 5 -> using chart -> we have last row -> ((277500- 166290) * (9.85 / 100)) + 11717.65 -> 22671.835
        # Step 6 -> Convert back to pay period amount and round
        # wh = -436.0
        # Add additional_withholding
        # wh = -436.0 + 40.0
        wh = -476.0

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MN'),
                                        mn_w4mn_sit_filing_status='single',
                                        state_income_tax_additional_withholding=40.0,
                                        mn_w4mn_sit_allowances=2.0,
                                        schedule_pay='weekly')

        self._log('2019 Minnesota tax first payslip additional withholding:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.MN_UNEMP)
        self.assertPayrollAlmostEqual(cats['EE_US_SIT'], wh)
