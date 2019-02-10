from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip


class TestUsCAPayslip(TestUsPayslip):
    ###
    #    Taxes and Rates
    ###
    CA_UIT_MAX_WAGE = 7000
    CA_UIT_MAX_WAGE = 7000
    CA_SDI_MAX_WAGE = 18371

    CA_UIT = -3.4 / 100.0
    CA_ETT = -0.1 / 100.0
    CA_SDI = -1.0 / 100.0

    # Examples from http://www.edd.ca.gov/pdf_pub_ctr/18methb.pdf
    def test_example_a(self):
        salary = 210
        schedule_pay = 'weekly'
        allowances = 1
        additional_allowances = 0

        wh = 0.00

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref(
                                            'l10n_us_ca_hr_payroll.hr_payroll_salary_structure_us_ca_employee'),
                                        schedule_pay=schedule_pay)
        contract.ca_c4_exemptions = allowances
        contract.ca_additional_allowances = additional_allowances
        contract.ca_de4_filing_status = 'single'

        self.assertEqual(contract.schedule_pay, 'weekly')

        self._log('2018 California tax last payslip:')
        payslip = self._createPayslip(employee, '2018-12-01', '2018-12-31')
        payslip.compute_sheet()
        process_payslip(payslip)

        self._log('2019 California tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_CA_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_CA_UNEMP'], cats['WAGE_US_CA_UNEMP'] * self.CA_UIT)
        self.assertPayrollEqual(cats['WAGE_US_CA_ETT'], salary)
        self.assertPayrollEqual(cats['ER_US_CA_ETT'], cats['WAGE_US_CA_ETT'] * self.CA_ETT)
        self.assertPayrollEqual(cats['WAGE_US_CA_SDI'], salary)
        self.assertPayrollEqual(cats['EE_US_CA_SDI'], cats['WAGE_US_CA_SDI'] * self.CA_SDI)
        self.assertPayrollEqual(cats['EE_US_CA_INC_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_ca_uit_wages = self.CA_UIT_MAX_WAGE - salary if (self.CA_UIT_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2019 California tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_CA_UNEMP'], remaining_ca_uit_wages)
        self.assertPayrollEqual(cats['ER_US_CA_UNEMP'], remaining_ca_uit_wages * self.CA_UIT)

    def test_example_b(self):
        salary = 1250
        schedule_pay = 'bi-weekly'
        allowances = 2
        additional_allowances = 1

        # for additional allowances
        wh = salary - 38
        wh = wh - 339
        wh = (wh - 632) * 0.022 + 6.95
        wh = wh - 9.65
        # 2.651 - 9.65
        wh = -wh

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref(
                                            'l10n_us_ca_hr_payroll.hr_payroll_salary_structure_us_ca_employee'),
                                        schedule_pay=schedule_pay)
        contract.ca_de4_allowances = allowances
        contract.ca_additional_allowances = additional_allowances
        contract.ca_de4_filing_status = 'married'

        self.assertEqual(contract.schedule_pay, 'bi-weekly')
        self.assertEqual(contract.ca_de4_filing_status, 'married')
        self.assertEqual(contract.ca_de4_allowances, 2)
        self.assertEqual(contract.ca_additional_allowances, 1)

        self._log('2018 California tax last payslip:')
        payslip = self._createPayslip(employee, '2018-12-01', '2018-12-31')
        payslip.compute_sheet()
        process_payslip(payslip)

        self._log('2019 California tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_CA_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_CA_UNEMP'], round((cats['WAGE_US_CA_UNEMP'] * self.CA_UIT), 2))
        self.assertPayrollEqual(cats['WAGE_US_CA_ETT'], salary)
        self.assertPayrollEqual(cats['ER_US_CA_ETT'], round((cats['WAGE_US_CA_ETT'] * self.CA_ETT), 2))
        self.assertPayrollEqual(cats['WAGE_US_CA_SDI'], salary)
        self.assertPayrollEqual(cats['EE_US_CA_SDI'], round((cats['WAGE_US_CA_SDI'] * self.CA_SDI), 2))
        self.assertPayrollEqual(cats['EE_US_CA_INC_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_ca_uit_wages = self.CA_UIT_MAX_WAGE - salary if (self.CA_UIT_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2019 California tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_CA_UNEMP'], remaining_ca_uit_wages)
        self.assertPayrollEqual(cats['ER_US_CA_UNEMP'], round((remaining_ca_uit_wages * self.CA_UIT), 2))

    def test_example_c(self):
        salary = 3800
        schedule_pay = 'monthly'
        allowances = 5
        additional_allowances = 0.72

        wh = -0.11

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref(
                                            'l10n_us_ca_hr_payroll.hr_payroll_salary_structure_us_ca_employee'),
                                        schedule_pay=schedule_pay)
        contract.ca_de4_allowances = allowances
        contract.ca_additional_allowances = additional_allowances
        contract.ca_de4_filing_status = 'married'

        self.assertEqual(contract.schedule_pay, 'monthly')
        self.assertEqual(contract.ca_de4_filing_status, 'married')
        self.assertEqual(contract.ca_de4_allowances, 5)
        self.assertEqual(contract.ca_additional_allowances, 0)

        self._log('2018 California tax last payslip:')
        payslip = self._createPayslip(employee, '2018-12-01', '2018-12-31')
        payslip.compute_sheet()
        process_payslip(payslip)

        self._log('2019 California tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_CA_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_CA_UNEMP'], round((cats['WAGE_US_CA_UNEMP'] * self.CA_UIT), 2))
        self.assertPayrollEqual(cats['WAGE_US_CA_ETT'], salary)
        self.assertPayrollEqual(cats['ER_US_CA_ETT'], round((cats['WAGE_US_CA_ETT'] * self.CA_ETT), 2))
        self.assertPayrollEqual(cats['WAGE_US_CA_SDI'], salary)
        self.assertPayrollEqual(cats['EE_US_CA_SDI'], round((cats['WAGE_US_CA_SDI'] * self.CA_SDI), 2))
        self.assertPayrollEqual(cats['EE_US_CA_INC_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_ca_uit_wages = self.CA_UIT_MAX_WAGE - salary if (self.CA_UIT_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2019 California tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_CA_UNEMP'], remaining_ca_uit_wages)
        self.assertPayrollEqual(cats['ER_US_CA_UNEMP'], round((remaining_ca_uit_wages * self.CA_UIT), 2))

    def test_example_d(self):
        salary = 800
        schedule_pay = 'weekly'
        allowances = 3
        additional_allowances = 0

        wh = -3.18

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref(
                                            'l10n_us_ca_hr_payroll.hr_payroll_salary_structure_us_ca_employee'),
                                        schedule_pay=schedule_pay)
        contract.ca_de4_allowances = allowances
        contract.ca_additional_allowances = additional_allowances
        contract.ca_de4_filing_status = 'head_household'

        self.assertEqual(contract.schedule_pay, 'weekly')
        self.assertEqual(contract.ca_de4_filing_status, 'head_household')
        self.assertEqual(contract.ca_de4_allowances, 3)
        self.assertEqual(contract.ca_additional_allowances, 0)

        self._log('2018 California tax last payslip:')
        payslip = self._createPayslip(employee, '2018-12-01', '2018-12-31')
        payslip.compute_sheet()
        process_payslip(payslip)

        self._log('2019 California tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_CA_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_CA_UNEMP'], round((cats['WAGE_US_CA_UNEMP'] * self.CA_UIT), 2))
        self.assertPayrollEqual(cats['WAGE_US_CA_ETT'], salary)
        self.assertPayrollEqual(cats['ER_US_CA_ETT'], round((cats['WAGE_US_CA_ETT'] * self.CA_ETT), 2))
        self.assertPayrollEqual(cats['WAGE_US_CA_SDI'], salary)
        self.assertPayrollEqual(cats['EE_US_CA_SDI'], round((cats['WAGE_US_CA_SDI'] * self.CA_SDI), 2))
        self.assertPayrollEqual(cats['EE_US_CA_INC_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_ca_uit_wages = self.CA_UIT_MAX_WAGE - salary if (self.CA_UIT_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2019 California tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_CA_UNEMP'], remaining_ca_uit_wages)
        self.assertPayrollEqual(cats['ER_US_CA_UNEMP'], round((remaining_ca_uit_wages * self.CA_UIT), 2))

    def test_example_e(self):
        salary = 1800
        schedule_pay = 'semi-monthly'
        allowances = 4
        additional_allowances = 0

        wh = -3.08

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref(
                                            'l10n_us_ca_hr_payroll.hr_payroll_salary_structure_us_ca_employee'),
                                        schedule_pay=schedule_pay)
        contract.ca_de4_allowances = allowances
        contract.ca_additional_allowances = additional_allowances
        contract.ca_de4_filing_status = 'married'

        self.assertEqual(contract.schedule_pay, 'semi-monthly')
        self.assertEqual(contract.ca_de4_filing_status, 'married')
        self.assertEqual(contract.ca_de4_allowances, 4)
        self.assertEqual(contract.ca_additional_allowances, 0)

        self._log('2018 California tax last payslip:')
        payslip = self._createPayslip(employee, '2018-12-01', '2018-12-31')
        payslip.compute_sheet()
        process_payslip(payslip)

        self._log('2019 California tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_CA_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_CA_UNEMP'], round((cats['WAGE_US_CA_UNEMP'] * self.CA_UIT), 2))
        self.assertPayrollEqual(cats['WAGE_US_CA_ETT'], salary)
        self.assertPayrollEqual(cats['ER_US_CA_ETT'], round((cats['WAGE_US_CA_ETT'] * self.CA_ETT), 2))
        self.assertPayrollEqual(cats['WAGE_US_CA_SDI'], salary)
        self.assertPayrollEqual(cats['EE_US_CA_SDI'], round((cats['WAGE_US_CA_SDI'] * self.CA_SDI), 2))
        self.assertPayrollEqual(cats['EE_US_CA_INC_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_ca_uit_wages = self.CA_UIT_MAX_WAGE - salary if (self.CA_UIT_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2019 California tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_CA_UNEMP'], remaining_ca_uit_wages)
        self.assertPayrollEqual(cats['ER_US_CA_UNEMP'], round((remaining_ca_uit_wages * self.CA_UIT), 2))

    def test_example_f(self):
        salary = 45000
        schedule_pay = 'annually'
        allowances = 4
        additional_allowances = 0

        wh = -113.85

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref(
                                            'l10n_us_ca_hr_payroll.hr_payroll_salary_structure_us_ca_employee'),
                                        schedule_pay=schedule_pay)
        contract.ca_de4_allowances = allowances
        contract.ca_additional_allowances = additional_allowances
        contract.ca_de4_filing_status = 'married'

        self.assertEqual(contract.schedule_pay, 'annually')
        self.assertEqual(contract.ca_de4_filing_status, 'married')
        self.assertEqual(contract.ca_de4_allowances, 4)
        self.assertEqual(contract.ca_additional_allowances, 0)

        self._log('2018 California tax last payslip:')
        payslip = self._createPayslip(employee, '2018-12-01', '2018-12-31')
        payslip.compute_sheet()
        process_payslip(payslip)

        self._log('2019 California tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_CA_UNEMP'], round((cats['WAGE_US_CA_UNEMP'] * self.CA_UIT), 2))
        self.assertPayrollEqual(cats['ER_US_CA_ETT'], round((cats['WAGE_US_CA_ETT'] * self.CA_ETT), 2))
        self.assertPayrollEqual(cats['EE_US_CA_SDI'], round((cats['WAGE_US_CA_SDI'] * self.CA_SDI), 2))
        self.assertPayrollEqual(cats['EE_US_CA_INC_WITHHOLD'], wh)

        process_payslip(payslip)

    def test_estimated_deduction_table(self):
        salary = 600
        allowances = 5
        schedule_pay = 'bi-weekly'
        expected_deduction = 192
        deduction = 0
        taxable_pay = 0
        estimated_deduction_table = {
            'weekly': (19, 38, 58, 77, 96, 115, 135, 154, 173, 192),
            'bi-weekly': (38, 77, 115, 154, 192, 231, 269, 308, 346, 385),
            'semi-monthly': (42, 83, 125, 167, 208, 250, 292, 333, 375, 417),
            'monthly': (83, 167, 250, 333, 417, 500, 583, 667, 750, 833),
            'quarterly': (250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 2500),
            'semi-annual': (500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000),
            'annual': (1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000),
        }

        allowance_index = allowances - 1
        if allowances > 10:
            deduction = (estimated_deduction_table[schedule_pay][0]) * allowances
            taxable_pay = salary - deduction
        elif allowances > 0:
            deduction = estimated_deduction_table[schedule_pay][allowance_index]
            taxable_pay = salary - deduction

        self.assertEqual(expected_deduction, deduction)
        self.assertTrue(taxable_pay < salary)
        self.assertEqual(taxable_pay, salary - deduction)

    def test_standard_deduction_table(self):
        salary = 3000
        schedule_pay = 'monthly'
        filing_status = 'head_household'
        expected_deduction = 706
        deduction = 0
        taxable_pay = 0
        standard_deduction_table = {
            'weekly': (81, 81, 163, 163),
            'bi-weekly': (163, 163, 326, 326),
            'semi-monthly': (177, 177, 353, 353),
            'monthly': (353, 352, 706, 706),
            'quarterly': (1059, 1059, 2188, 2188),
            'semi-annual': (2118, 2118, 4236, 4236),
            'annual': (4236, 4236, 8471, 8472),
        }

        if filing_status == 'head_household':
            _, _, _, deduction = standard_deduction_table[schedule_pay]
            taxable_pay = salary - deduction
        elif filing_status == 'married':
            if allowances >= 2:
                _, _, deduction, _ = standard_deduction_table[schedule_pay]
                taxable_pay = salary - deduction
            else:
                _, deduction, _, _ = standard_deduction_table[schedule_pay]
                taxable_pay = salary - deduction
        else:
            deduction, _, _, _ = standard_deduction_table[schedule_pay]
            taxable_pay = salary - deduction

        self.assertEqual(expected_deduction, deduction)
        self.assertTrue(taxable_pay < salary)
        self.assertEqual(taxable_pay, salary - deduction)
