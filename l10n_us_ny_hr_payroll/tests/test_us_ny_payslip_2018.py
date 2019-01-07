from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip


class TestUsNYPayslip(TestUsPayslip):
    ###
    #    Taxes and Rates
    ###
    NY_UNEMP_MAX_WAGE = 11100

    # Examples from http://www.edd.ca.gov/pdf_pub_ctr/18methb.pdf
    def test_single_example1(self):
        salary = 400
        schedule_pay = 'weekly'
        allowances = 3
        additional_withholding = 0

        wh = -8.20

        employee = self._createEmployee()
        employee.company_id.ny_unemp_rate_2018 = 0.825
        employee.company_id.ny_rsf_rate_2018 = 0.075
        employee.company_id.ny_mctmt_rate_2018 = 0.0

        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref(
                                            'l10n_us_ny_hr_payroll.hr_payroll_salary_structure_us_ny_employee'),
                                        schedule_pay=schedule_pay)
        contract.ny_it2104_allowances = allowances
        contract.ny_additional_withholding = additional_withholding
        contract.ny_it2104_filing_status = 'single'

        self.assertEqual(contract.schedule_pay, 'weekly')

        # tax rates
        ny_unemp = contract.ny_unemp_rate(2018) / -100.0
        ny_rsf = contract.ny_rsf_rate(2018) / -100.0
        ny_mctmt = contract.ny_mctmt_rate(2018) / -100.0

        self._log('2018 New York tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NY_UNEMP_WAGES'], salary)
        self.assertPayrollEqual(cats['NY_UNEMP'], cats['NY_UNEMP_WAGES'] * ny_unemp)
        self.assertPayrollEqual(cats['NY_RSF'], cats['NY_UNEMP_WAGES'] * ny_rsf)
        self.assertPayrollEqual(cats['NY_MCTMT'], cats['NY_UNEMP_WAGES'] * ny_mctmt)
        self.assertPayrollEqual(cats['NY_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_ny_unemp_wages = self.NY_UNEMP_MAX_WAGE - salary if (self.NY_UNEMP_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2018 New York tax second payslip:')
        payslip = self._createPayslip(employee, '2018-02-01', '2018-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NY_UNEMP_WAGES'], remaining_ny_unemp_wages)
        self.assertPayrollEqual(cats['NY_UNEMP'], remaining_ny_unemp_wages * ny_unemp)

    def test_single_example2(self):
        salary = 5000
        schedule_pay = 'semi-monthly'
        allowances = 3
        additional_withholding = 0

        wh = -284.19

        employee = self._createEmployee()
        employee.company_id.ny_unemp_rate_2018 = 0.825
        employee.company_id.ny_rsf_rate_2018 = 0.075
        employee.company_id.ny_mctmt_rate_2018 = 0.0

        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref(
                                            'l10n_us_ny_hr_payroll.hr_payroll_salary_structure_us_ny_employee'),
                                        schedule_pay=schedule_pay)
        contract.ny_it2104_allowances = allowances
        contract.ny_additional_withholding = additional_withholding
        contract.ny_it2104_filing_status = 'married'

        self.assertEqual(contract.schedule_pay, 'semi-monthly')

        # tax rates
        ny_unemp = contract.ny_unemp_rate(2018) / -100.0
        ny_rsf = contract.ny_rsf_rate(2018) / -100.0
        ny_mctmt = contract.ny_mctmt_rate(2018) / -100.0

        self._log('2018 New York tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NY_UNEMP_WAGES'], salary)
        self.assertPayrollEqual(cats['NY_UNEMP'], cats['NY_UNEMP_WAGES'] * ny_unemp)
        self.assertPayrollEqual(cats['NY_RSF'], cats['NY_UNEMP_WAGES'] * ny_rsf)
        self.assertPayrollEqual(cats['NY_MCTMT'], cats['NY_UNEMP_WAGES'] * ny_mctmt)
        self.assertPayrollEqual(cats['NY_WITHHOLD'], wh)

        process_payslip(payslip)

    def test_single_example3(self):
        salary = 50000
        schedule_pay = 'monthly'
        allowances = 3
        additional_withholding = 0

        wh = -3575.63

        employee = self._createEmployee()
        employee.company_id.ny_unemp_rate_2018 = 0.825
        employee.company_id.ny_rsf_rate_2018 = 0.075
        employee.company_id.ny_mctmt_rate_2018 = 0.0

        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref(
                                            'l10n_us_ny_hr_payroll.hr_payroll_salary_structure_us_ny_employee'),
                                        schedule_pay=schedule_pay)
        contract.ny_it2104_allowances = allowances
        contract.ny_additional_withholding = additional_withholding
        contract.ny_it2104_filing_status = 'single'

        self.assertEqual(contract.schedule_pay, 'monthly')

        # tax rates
        ny_unemp = contract.ny_unemp_rate(2018) / -100.0
        ny_rsf = contract.ny_rsf_rate(2018) / -100.0
        ny_mctmt = contract.ny_mctmt_rate(2018) / -100.0

        self._log('2018 New York tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NY_WITHHOLD'], wh)

