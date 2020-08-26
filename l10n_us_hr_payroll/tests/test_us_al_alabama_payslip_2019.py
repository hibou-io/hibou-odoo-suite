# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip


class TestUsALPayslip(TestUsPayslip):
    # TAXES AND RATES
    AL_UNEMP_MAX_WAGE = 8000.00
    AL_UNEMP = -2.70 / 100.0

    def test_taxes_weekly(self):
        salary = 10000.00
        schedule_pay = 'weekly'
        dependents = 1
        filing_status = 'S'
        # see https://revenue.alabama.gov/wp-content/uploads/2019/01/whbooklet_0119.pdf for reference
        # Hand Calculated Amount to Test
        # Step 1 -> 10000.00 for wages per period , 52.0 for weekly -> 10000 * 52 -> 520000.0
        # Step 2A -> standard deduction for highest wage bracket -> 2000. Subtract from yearly income
        #           520000 - 2000 = 518000.0
        # Step 2B -> Subtract  Federal Income Tax in yearly form -> Our Fed withholding is -2999.66 * 52 = -155982.32
        #         -> 518000.0 - 155982.32 = 362017.68
        # Step 2C -> Subtract the personal exemption ->  1500 for single filing_status
        #         -> 362017.68 - 1500 = 360517.68
        # Step 2D -> Since income is so high, only 300$ per dependent -> 300$. Subtract
        #         -> 360517.68 - 300 = 360217.68
        #
        # Step 5 (after adding previous lines) -> Compute marginal taxes.
        # (500 * (2.00 / 100)) + (2500 * (4.00 / 100)) + ((360217.68 - 500 - 2500) * (5.00 / 100)) -> 17970.884000000002
        # Convert back to pay period
        # wh = round(17970.884000000002, 2) -> 17970.88 / 52.0 -> 345.59
        wh = -345.59

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('AL'),
                                        al_a4_sit_exemptions=filing_status,
                                        state_income_tax_additional_withholding=0.0,
                                        state_income_tax_exempt=False,
                                        al_a4_sit_dependents=dependents,
                                        schedule_pay=schedule_pay)

        self._log('2019 Alabama tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_941_FIT'], -2999.66)  # Hand Calculated.
        self.assertPayrollEqual(cats['ER_US_SUTA'], self.AL_UNEMP_MAX_WAGE * self.AL_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)

        remaining_AL_UNEMP_wages = 0.00  # We already reached the maximum wage for unemployment insurance.

        self._log('2019 Alabama tax second payslip weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_AL_UNEMP_wages * self.AL_UNEMP)  # 0

    def test_taxes_married_jointly(self):
        salary = 10000.00
        schedule_pay = 'weekly'
        dependents = 1
        filing_status = 'M'

        # see https://revenue.alabama.gov/wp-content/uploads/2019/01/whbooklet_0119.pdf for reference
        # Hand Calculated Amount to Test
        # Step 1 -> 10000.00 for wages per period , 52.0 for weekly -> 10000 * 52 -> 520000.0
        # Step 2A -> standard deduction for highest wage bracket -> 4000. Subtract from yearly income
        #           520000 - 4000 = 516000.0
        # Step 2B -> Subtract  Federal Income Tax in yearly form -> Our Fed withholding is -2999.66 * 52 = -155982.32
        #         -> 516000.0 - 155982.32 = 360017.68
        # Step 2C -> Subtract the personal exemption ->  3000 for married filing jointly.
        #         -> 360017.68 - 3000 = 357017.68
        # Step 2D -> Since income is so high, only 300$ per dependent -> 300$. Subtract
        #         -> 357017.68 - 300 = 356717.68
        #
        # Step 5 (after adding previous lines) -> Compute marginal taxes.
        # (1000 * (2.00 / 100)) + (5000 * (4.00 / 100)) + ((356717.68 - 1000 - 50000) * (5.00 / 100))
        #       -> 17755.884000000002
        # Convert back to pay period
        # wh = round(17755.884000000002, 2) -> 15505.88 / 52.0 -> 341.45923076923077
        wh = -341.46

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('AL'),
                                        al_a4_sit_exemptions=filing_status,
                                        state_income_tax_additional_withholding=0.0,
                                        state_income_tax_exempt=False,
                                        al_a4_sit_dependents=dependents,
                                        schedule_pay=schedule_pay)

        self._log('2019 Alabama tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_941_FIT'], -2999.66)  # Hand Calculated.
        self.assertPayrollEqual(cats['ER_US_SUTA'], self.AL_UNEMP_MAX_WAGE * self.AL_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)


    def test_taxes_semimonthly_filing_seperate(self):
        salary = 20000.00
        schedule_pay = 'monthly'
        filing_status = 'MS'
        dependents = 2

        # see https://revenue.alabama.gov/wp-content/uploads/2019/01/whbooklet_0119.pdf for reference
        # Hand Calculated Amount to Test
        # Step 1 -> 10000.00 for wages per period , 12.0 for monthly -> 20000 * 12 -> 240000.00
        # Step 2A -> standard deduction for highest wage bracket -> 2000. Subtract from yearly income
        #           240000.00 - 2000 = 238000.00
        # Step 2B -> Subtract  Federal Income Tax in yearly form -> Our Fed withholding is -4821.99 * 12 = -57863.88
        #         -> 238000.00 - 57863.88 = 180136.12
        # Step 2C -> Subtract the personal exemption ->  1500 for married filing separately
        #         -> 180136.12 - 1500 = 178636.12
        # Step 2D -> Since income is so high, only 300$ per dependent -> 600. Subtract
        #         -> 178636.12 - 600 = 178036.12
        #
        # Step 5 (after adding previous lines) -> Compute marginal taxes.
        # (500 * (2.00 / 100)) + (2500 * (4.00 / 100)) + ((178036.12 - 500 - 2500) * (5.00 / 100)) -> 8861.806
        # Convert back to pay period
        # wh = 8861.806 / 12.0 rounded -> 738.48
        wh = -738.48

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('AL'),
                                        al_a4_sit_exemptions=filing_status,
                                        state_income_tax_additional_withholding=0.0,
                                        state_income_tax_exempt=False,
                                        al_a4_sit_dependents=dependents,
                                        schedule_pay=schedule_pay)

        self._log('2019 Alabama tax first payslip monthly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_941_FIT'], -4822.00)  # Hand Calculated.
        self.assertPayrollEqual(cats['ER_US_SUTA'], self.AL_UNEMP_MAX_WAGE * self.AL_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)

    def test_tax_exempt(self):
        salary = 5500.00
        wh = 0
        schedule_pay = 'weekly'
        dependents = 2

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('AL'),
                                        al_a4_sit_exemptions='',
                                        state_income_tax_additional_withholding=0.0,
                                        state_income_tax_exempt=True,
                                        al_a4_sit_dependents=dependents,
                                        schedule_pay=schedule_pay)

        self._log('2019 Alabama tax first payslip exempt:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.AL_UNEMP)
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), wh)

    def test_additional_withholding(self):
        salary = 5500.0
        schedule_pay = 'weekly'
        additional_wh = 40.0
        dependents = 2
        # filing status default is single

        # see https://revenue.alabama.gov/wp-content/uploads/2019/01/whbooklet_0119.pdf for reference
        # Hand Calculated Amount to Test
        # Step 1 -> 5500.00 for wages per period , 52.0 for monthly -> 5500 * 52.0 -> 286000.0
        # Step 2A -> standard deduction for highest wage bracket -> 2000. Subtract from yearly income
        #           286000.0 - 2000 = 284000.0
        # Step 2B -> Subtract  Federal Income Tax in yearly form -> Our Fed withholding is -1422.4 * 52.0 = -73964.8
        #         -> 284000.0 - 73964.8 = 210035.2
        # Step 2C -> Subtract the personal exemption ->  1500 for single
        #         -> 210035.2 - 1500 = 208535.2
        # Step 2D -> Since income is so high, only 300$ per dependent -> 600. Subtract
        #         -> 208535.2 - 600 = 207935.2
        #
        # Step 5 (after adding previous lines) -> Compute marginal taxes.
        # (500 * (2.00 / 100)) + (2500 * (4.00 / 100)) + ((207935.2 - 500 - 2500) * (5.00 / 100)) -> 10356.76
        # Convert back to pay period
        # wh = 10356.76 / 52.0 rounded -> 199.17
        wh = -199.17

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('AL'),
                                        al_a4_sit_exemptions='S',
                                        state_income_tax_additional_withholding=40.0,
                                        state_income_tax_exempt=False,
                                        al_a4_sit_dependents=dependents,
                                        schedule_pay=schedule_pay)

        self._log('2019 Alabama tax first payslip additional withholding:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_941_FIT'], -1422.4)  # Hand Calculated.
        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.AL_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh - additional_wh)

    def test_personal_exemption(self):
        salary = 5500.0
        schedule_pay = 'weekly'
        # filing status default is single

        # see https://revenue.alabama.gov/wp-content/uploads/2019/01/whbooklet_0119.pdf for reference
        # Hand Calculated Amount to Test
        # Step 1 -> 5500.00 for wages per period , 52.0 for monthly -> 5500 * 52.0 -> 286000.0
        # Step 2A -> standard deduction for highest wage bracket -> 2000. Subtract from yearly income
        #           286000.0 - 2000 = 284000.0
        # Step 2B -> Subtract  Federal Income Tax in yearly form -> Our Fed withholding is -1422.4 * 52.0 = -73964.8
        #         -> 284000.0 - 73964.8 = 210035.2
        # Step 2C -> Subtract the personal exemption ->  0 for personal exemptioon
        #         -> 210035.2 - 0 = 210035.2
        # Step 2D -> Subtract per dependent. No dependents so 0
        #         -> 210035.2 - 0 = 210035.2
        #
        # Step 5 (after adding previous lines) -> Compute marginal taxes.
        # (500 * (2.00 / 100)) + (2500 * (4.00 / 100)) + ((210035.2 - 500 - 2500) * (5.00 / 100)) -> 10461.76
        # Convert back to pay period
        # wh = 10461.76 / 52.0 rounded -> 201.19
        wh = -199.74

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('AL'),
                                        al_a4_sit_exemptions='S',
                                        state_income_tax_additional_withholding=0.0,
                                        state_income_tax_exempt=False,
                                        al_a4_sit_dependents=0.0,
                                        schedule_pay=schedule_pay)

        self._log('2019 Alabama tax first payslip additional withholding:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_941_FIT'], -1422.4)  # Hand Calculated.
        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.AL_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)
