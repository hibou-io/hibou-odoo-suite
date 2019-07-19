from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip
from odoo.addons.l10n_us_hr_payroll.models.l10n_us_hr_payroll import USHrContract


class TestUsARPayslip(TestUsPayslip):

    AR_UNEMP_MAX_WAGE = 10000.00
    AR_UNEMP = -3.2 / 100.0
    AR_INC_TAX = -0.0535

    def test_taxes_monthly(self):
        salary = 10000.0
        schedule_pay = 'monthly'

        employee = self._createEmployee()
        contract = self._createContract(employee, salary,
                                        struct_id=self.ref('l10n_us_ar_hr_payroll.hr_payroll_salary_structure_us_ar_employee'),
                                        schedule_pay=schedule_pay)

        self.assertEqual(contract.schedule_pay, 'monthly')

        self._log('2019 Arkansas tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        # Not exempt from rule 1 or rule 2 - unemployment wages., and actual unemployment.
        self.assertPayrollEqual(cats['WAGE_US_AR_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_AR_UNEMP'], cats['WAGE_US_AR_UNEMP'] * self.AR_UNEMP)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums
        remaining_AR_UNEMP_wages = self.AR_UNEMP_MAX_WAGE - salary if (self.AR_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary
        # We reached the cap of 10000.0 in the first payslip.
        self.assertEqual(0.0, remaining_AR_UNEMP_wages)
        self._log('2019 Arkansas tax second payslip weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_AR_UNEMP'], remaining_AR_UNEMP_wages)
        self.assertPayrollEqual(cats['ER_US_AR_UNEMP'], remaining_AR_UNEMP_wages * self.AR_UNEMP)

    def test_taxes_with_state_exempt(self):
        salary = 50000.0
        tax_exempt = True   # State withholding should be zero.

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref('l10n_us_ar_hr_payroll.hr_payroll_salary_structure_us_ar_employee'),
                                        )
        contract.ar_w4_tax_exempt = tax_exempt

        self._log('2019 Arkansas exempt tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_AR_UNEMP'], self.AR_UNEMP_MAX_WAGE)
        self.assertPayrollEqual(cats.get('ER_US_AR_UNEMP', 0.0), cats.get('WAGE_US_AR_UNEMP', 0.0) * self.AR_UNEMP)
        self.assertPayrollEqual(cats.get('EE_US_AR_INC_WITHHOLD', 0.0), 0.0)

        process_payslip(payslip)

    def test_taxes_with_texarkana_exempt(self):
        salary = 40000.00
        texarkana_exemption = True  # State withholding should be zero.

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref('l10n_us_ar_hr_payroll.hr_payroll_salary_structure_us_ar_employee'))
        contract.ar_w4_texarkana_exemption = texarkana_exemption

        self._log('2019 Arkansas tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats.get('WAGE_US_AR_UNEMP', 0.0), self.AR_UNEMP_MAX_WAGE)
        self.assertPayrollEqual(cats.get('ER_US_AR_UNEMP', 0.0), cats.get('WAGE_US_AR_UNEMP', 0.0) * self.AR_UNEMP)

        process_payslip(payslip)

    def test_additional_withholding(self):
        wages = 5000.0
        schedule_pay = 'monthly'
        pay_periods = 12
        additional_wh = 150.0
        exemptions = 2
        # TODO: comment on how it was calculated
        test_ar_amt = 3069.97

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wages,
                                        struct_id=self.ref('l10n_us_ar_hr_payroll.hr_payroll_salary_structure_us_ar_employee'),
                                        schedule_pay=schedule_pay)
        contract.ar_w4_additional_wh = 0.0
        contract.ar_w4_allowances = exemptions

        self.assertEqual(contract.schedule_pay, 'monthly')

        self._log('2019 Arkansas tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_AR_UNEMP'], wages)
        self.assertPayrollEqual(cats['ER_US_AR_UNEMP'], cats['WAGE_US_AR_UNEMP'] * self.AR_UNEMP)
        # TODO: change to hand the test_ar_amt already be divided by pay periods
        self.assertPayrollEqual(cats['EE_US_AR_INC_WITHHOLD'], -(test_ar_amt / pay_periods))

        contract.ar_w4_additional_wh = additional_wh
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_AR_INC_WITHHOLD'], -(test_ar_amt / pay_periods) - additional_wh)

        process_payslip(payslip)

    def test_under_fifty_thousand(self):
        wages = 2500.00
        schedule_pay = 'monthly'
        pay_periods = 12
        additional_wh = 150.0
        exemptions = 2
        # TODO: comment calc.
        test_ar_amt = 1066.151

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wages,
                                        struct_id=self.ref(
                                            'l10n_us_ar_hr_payroll.hr_payroll_salary_structure_us_ar_employee'),
                                        schedule_pay=schedule_pay)
        contract.ar_w4_additional_wh = 0.0
        contract.ar_w4_allowances = exemptions

        self.assertEqual(contract.schedule_pay, 'monthly')

        self._log('2019 Arkansas tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_AR_UNEMP'], wages)
        self.assertPayrollEqual(cats['ER_US_AR_UNEMP'], cats['WAGE_US_AR_UNEMP'] * self.AR_UNEMP)
        self.assertPayrollEqual(cats['EE_US_AR_INC_WITHHOLD'], -(test_ar_amt / pay_periods))

        contract.ar_w4_additional_wh = additional_wh
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats['EE_US_AR_INC_WITHHOLD'], -(test_ar_amt / pay_periods) - additional_wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_AR_UNEMP_wages = self.AR_UNEMP_MAX_WAGE - wages if (self.AR_UNEMP_MAX_WAGE - 2 * wages < wages) \
            else wages

        self._log('2019 Arkansas tax second payslip weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_AR_UNEMP'], remaining_AR_UNEMP_wages)
        self.assertPayrollEqual(cats['ER_US_AR_UNEMP'], remaining_AR_UNEMP_wages * self.AR_UNEMP)

    def test_over_fifty_thousand(self):
        wages = 10000.00  # 10000.00 monthly is over 50,000 annually.
        schedule_pay = 'monthly'
        pay_periods = 12
        additional_wh = 150.0
        exemptions = 2
        # TODO: comment on how it was calculated
        test_ar_amt = 7209.97

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wages,
                                        struct_id=self.ref(
                                            'l10n_us_ar_hr_payroll.hr_payroll_salary_structure_us_ar_employee'),
                                        schedule_pay=schedule_pay)
        contract.ar_w4_additional_wh = 0.0
        contract.ar_w4_allowances = exemptions

        self.assertEqual(contract.schedule_pay, 'monthly')

        self._log('2019 Arkansas tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_AR_UNEMP'], wages)
        self.assertPayrollEqual(cats['ER_US_AR_UNEMP'], cats['WAGE_US_AR_UNEMP'] * self.AR_UNEMP)
        self.assertPayrollEqual(cats['EE_US_AR_INC_WITHHOLD'], -(test_ar_amt / pay_periods))

        contract.ar_w4_additional_wh = additional_wh
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats['EE_US_AR_INC_WITHHOLD'], -(test_ar_amt / pay_periods) - additional_wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_AR_UNEMP_wages = self.AR_UNEMP_MAX_WAGE - wages if (self.AR_UNEMP_MAX_WAGE - 2 * wages < wages) \
            else wages

        self._log('2019 Arkansas tax second payslip weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_AR_UNEMP'], remaining_AR_UNEMP_wages)
        self.assertPayrollEqual(cats['ER_US_AR_UNEMP'], remaining_AR_UNEMP_wages * self.AR_UNEMP)

    def test_married(self):
        wages = 5500.00
        schedule_pay = 'monthly'
        pay_periods = 12
        additional_wh = 150.0
        exemptions = 2
        w4_filing_status = 'married'
        # TODO: explain calc.
        # Yearly -> 3332.17. Monthly -> 427.681
        test_ar_amt = 3332.17

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wages,
                                        struct_id=self.ref(
                                            'l10n_us_ar_hr_payroll.hr_payroll_salary_structure_us_ar_employee'),
                                        schedule_pay=schedule_pay)
        contract.ar_w4_additional_wh = additional_wh
        contract.ar_w4_allowances = exemptions
        contract.w4_filing_status = w4_filing_status

        self.assertEqual(contract.w4_filing_status, 'married')

        self._log('2019 Arkansas tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_AR_UNEMP'], wages)
        self.assertPayrollEqual(cats['ER_US_AR_UNEMP'], cats['WAGE_US_AR_UNEMP'] * self.AR_UNEMP)
        self.assertPayrollEqual(cats['EE_US_AR_INC_WITHHOLD'], -(test_ar_amt / pay_periods) - additional_wh)

    def test_single(self):
        wages = 5500.00
        schedule_pay = 'monthly'
        pay_periods = 12
        additional_wh = 150.0
        exemptions = 2
        w4_filling_status = 'single'
        # TODO: explain calc.
        # Yearly -> 3483.972 Monthly -> 298.331
        test_ar_amt = 3483.972

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wages,
                                        struct_id=self.ref(
                                            'l10n_us_ar_hr_payroll.hr_payroll_salary_structure_us_ar_employee'),
                                        schedule_pay=schedule_pay)
        contract.ar_w4_additional_wh = 0
        contract.ar_w4_allowances = exemptions
        contract.w4_filling_status = w4_filling_status

        self.assertEqual(contract.w4_filling_status, 'single')

        self._log('2019 Arkansas tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_AR_UNEMP'], wages)
        self.assertPayrollEqual(cats['ER_US_AR_UNEMP'], cats['WAGE_US_AR_UNEMP'] * self.AR_UNEMP)
        self.assertPayrollEqual(cats['EE_US_AR_INC_WITHHOLD'], -(test_ar_amt / pay_periods))

        contract.ar_w4_additional_wh = additional_wh
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats['EE_US_AR_INC_WITHHOLD'], -(test_ar_amt / pay_periods) - additional_wh)

        process_payslip(payslip)
