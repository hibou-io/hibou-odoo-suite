from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip
from odoo.addons.l10n_us_hr_payroll.l10n_us_hr_payroll import USHrContract


class TestUsNCPayslip(TestUsPayslip):
    ###
    #    Taxes and Rates
    ###
    NC_UNEMP_MAX_WAGE = 7000.0


    def test_2018_taxes_weekly(self):
        salary = 5000.0
        schedule_pay = 'weekly'
        # allowance_multiplier and Portion of Standard Deduction for weekly
        allowance_multiplier = 48.08
        PST = 168.27

        exemption = 1
        # Algorithm derived from percentage method in https://files.nc.gov/ncdor/documents/files/nc-30_book_web.pdf

        wh = -round((salary - (PST + (allowance_multiplier * exemption))) * 0.05599)

        employee = self._createEmployee()
        employee.company_id.nc_unemp_rate_2018 = 0.06

        contract = self._createContract(employee, salary, struct_id=self.ref('l10n_us_nc_hr_payroll.hr_payroll_salary_structure_us_nc_employee'), schedule_pay=schedule_pay)
        contract.nc_nc4_allowances = exemption

        self.assertEqual(contract.schedule_pay, 'weekly')

        # tax rates
        nc_unemp = contract.nc_unemp_rate(2018) / -100.0


        self._log('2018 North Carolina tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NC_UNEMP_WAGES'], salary)
        self.assertPayrollEqual(cats['NC_UNEMP'], cats['NC_UNEMP_WAGES'] * nc_unemp)
        self.assertPayrollEqual(cats['NC_INC_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_nc_unemp_wages = self.NC_UNEMP_MAX_WAGE - salary if (self.NC_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2018 North Carolina tax second payslip weekly:')
        payslip = self._createPayslip(employee, '2018-02-01', '2018-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NC_UNEMP_WAGES'], remaining_nc_unemp_wages)
        self.assertPayrollEqual(cats['NC_UNEMP'], remaining_nc_unemp_wages * nc_unemp)

    def test_2018_taxes_with_external_weekly(self):
        salary = 5000.0
        external_wages = 7000.0

        schedule_pay = 'weekly'

        employee = self._createEmployee()
        employee.company_id.nc_unemp_rate_2018 = 0.06

        contract = self._createContract(employee, salary, external_wages=external_wages,
                                        struct_id=self.ref('l10n_us_nc_hr_payroll.hr_payroll_salary_structure_us_nc_employee'), schedule_pay=schedule_pay)

        # tax rates
        nc_unemp = contract.nc_unemp_rate(2018) / -100.0

        self._log('2018 NorthCarolina_external tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NC_UNEMP_WAGES'], self.NC_UNEMP_MAX_WAGE - external_wages)
        self.assertPayrollEqual(cats['NC_UNEMP'], cats['NC_UNEMP_WAGES'] * nc_unemp)

    def test_2018_taxes_with_state_exempt_weekly(self):
        salary = 5000.0
        external_wages = 6000.0
        schedule_pay = 'weekly'

        employee = self._createEmployee()
        employee.company_id.nc_unemp_rate_2018 = 0.06

        contract = self._createContract(employee, salary, external_wages=external_wages, struct_id=self.ref(
            'l10n_us_nc_hr_payroll.hr_payroll_salary_structure_us_nc_employee'), futa_type=USHrContract.FUTA_TYPE_BASIC, schedule_pay=schedule_pay)

        # tax rates
        nc_unemp = contract.nc_unemp_rate(2018) / -100.0

        self.assertPayrollEqual(nc_unemp, 0.0)

        self._log('2018 North Carolina exempt tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NC_UNEMP_WAGES'], self.NC_UNEMP_MAX_WAGE - external_wages)
        self.assertPayrollEqual(cats['NC_UNEMP'], cats['NC_UNEMP_WAGES'] * nc_unemp)

    def test_2018_taxes_biweekly(self):
        salary = 5000.0
        schedule_pay = 'bi-weekly'
        # allowance_multiplier and Portion of Standard Deduction for weekly
        allowance_multiplier = 96.15
        PST = 336.54

        allowances = 2
        # Algorithm derived from percentage method in https://files.nc.gov/ncdor/documents/files/nc-30_book_web.pdf

        wh = -round((salary - (PST + (allowance_multiplier * allowances))) * 0.05599)

        employee = self._createEmployee()
        employee.company_id.nc_unemp_rate_2018 = 0.06

        contract = self._createContract(employee, salary, struct_id=self.ref('l10n_us_nc_hr_payroll.hr_payroll_salary_structure_us_nc_employee'), schedule_pay=schedule_pay)
        contract.nc_nc4_allowances = allowances

        self.assertEqual(contract.schedule_pay, 'bi-weekly')

        # tax rates
        nc_unemp = contract.nc_unemp_rate(2018) / -100.0


        self._log('2018 North Carolina tax first payslip bi-weekly:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NC_UNEMP_WAGES'], salary)
        self.assertPayrollEqual(cats['NC_UNEMP'], cats['NC_UNEMP_WAGES'] * nc_unemp)
        self.assertPayrollEqual(cats['NC_INC_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_nc_unemp_wages = self.NC_UNEMP_MAX_WAGE - salary if (self.NC_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2018 North Carolina tax second payslip bi-weekly:')
        payslip = self._createPayslip(employee, '2018-02-01', '2018-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NC_UNEMP_WAGES'], remaining_nc_unemp_wages)
        self.assertPayrollEqual(cats['NC_UNEMP'], remaining_nc_unemp_wages * nc_unemp)

    def test_2018_taxes_semimonthly(self):
        salary = 4000.0
        schedule_pay = 'semi-monthly'
        nc_nc4_filing_status = 'head_household'
        # allowance_multiplier and Portion of Standard Deduction for weekly
        allowance_multiplier = 104.17
        PST = 583.33

        allowances = 1
        # Algorithm derived from percentage method in https://files.nc.gov/ncdor/documents/files/nc-30_book_web.pdf

        wh = -round((salary - (PST + (allowance_multiplier * allowances))) * 0.05599)

        employee = self._createEmployee()
        employee.company_id.nc_unemp_rate_2018 = 0.06

        contract = self._createContract(employee, salary, struct_id=self.ref(
            'l10n_us_nc_hr_payroll.hr_payroll_salary_structure_us_nc_employee'), schedule_pay=schedule_pay)
        contract.nc_nc4_allowances = allowances
        contract.nc_nc4_filing_status = nc_nc4_filing_status

        self.assertEqual(contract.schedule_pay, 'semi-monthly')

        # tax rates
        nc_unemp = contract.nc_unemp_rate(2018) / -100.0

        self._log('2018 North Carolina tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NC_UNEMP_WAGES'], salary)
        self.assertPayrollEqual(cats['NC_UNEMP'], cats['NC_UNEMP_WAGES'] * nc_unemp)
        self.assertPayrollEqual(cats['NC_INC_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_nc_unemp_wages = self.NC_UNEMP_MAX_WAGE - salary if (self.NC_UNEMP_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2018 North Carolina tax second payslip:')
        payslip = self._createPayslip(employee, '2018-02-01', '2018-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NC_UNEMP_WAGES'], remaining_nc_unemp_wages)
        self.assertPayrollEqual(cats['NC_UNEMP'], remaining_nc_unemp_wages * nc_unemp)

    def test_2018_taxes_monthly(self):
        salary = 4000.0
        schedule_pay = 'monthly'
        # allowance_multiplier and Portion of Standard Deduction for weekly
        allowance_multiplier = 208.33
        PST = 729.17

        allowances = 1
        # Algorithm derived from percentage method in https://files.nc.gov/ncdor/documents/files/nc-30_book_web.pdf

        wh = -round((salary - (PST + (allowance_multiplier * allowances))) * 0.05599)

        employee = self._createEmployee()
        employee.company_id.nc_unemp_rate_2018 = 0.06

        contract = self._createContract(employee, salary, struct_id=self.ref(
            'l10n_us_nc_hr_payroll.hr_payroll_salary_structure_us_nc_employee'), schedule_pay=schedule_pay)
        contract.nc_nc4_allowances = allowances

        self.assertEqual(contract.schedule_pay, 'monthly')

        # tax rates
        nc_unemp = contract.nc_unemp_rate(2018) / -100.0

        self._log('2018 North Carolina tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NC_UNEMP_WAGES'], salary)
        self.assertPayrollEqual(cats['NC_UNEMP'], cats['NC_UNEMP_WAGES'] * nc_unemp)
        self.assertPayrollEqual(cats['NC_INC_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_nc_unemp_wages = self.NC_UNEMP_MAX_WAGE - salary if (
                    self.NC_UNEMP_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2018 North Carolina tax second payslip:')
        payslip = self._createPayslip(employee, '2018-02-01', '2018-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NC_UNEMP_WAGES'], remaining_nc_unemp_wages)
        self.assertPayrollEqual(cats['NC_UNEMP'], remaining_nc_unemp_wages * nc_unemp)

    def test_tax_exempt(self):
        salary = 4000.0
        wh = 0
        schedule_pay = 'weekly'
        excemptions = 1

        employee = self._createEmployee()
        employee.company_id.nc_unemp_rate_2018 = 0.06

        contract = self._createContract(employee, salary, struct_id=self.ref(
            'l10n_us_nc_hr_payroll.hr_payroll_salary_structure_us_nc_employee'), schedule_pay=schedule_pay)
        contract.nc_nc4_allowances = excemptions
        contract.nc_nc4_filing_status = 'exempt'

        self.assertEqual(contract.schedule_pay, 'weekly')

        # tax rates
        nc_unemp = contract.nc_unemp_rate(2018) / -100.0


        self._log('2018 North Carolina tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NC_UNEMP_WAGES'], salary)
        self.assertPayrollEqual(cats['NC_UNEMP'], cats['NC_UNEMP_WAGES'] * nc_unemp)
        self.assertPayrollEqual(cats['NC_INC_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_nc_unemp_wages = self.NC_UNEMP_MAX_WAGE - salary if (
                    self.NC_UNEMP_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2018 North Carolina tax second payslip:')
        payslip = self._createPayslip(employee, '2018-02-01', '2018-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NC_UNEMP_WAGES'], remaining_nc_unemp_wages)
        self.assertPayrollEqual(cats['NC_UNEMP'], remaining_nc_unemp_wages * nc_unemp)

    def test_additional_withholding(self):
        salary = 4000.0
        schedule_pay = 'weekly'
        # allowance_multiplier and Portion of Standard Deduction for weekly
        allowance_multiplier = 48.08
        PST = 168.27
        additional_wh = 40.0

        #4000 - (168.27 + (48.08 * 1)

        allowances = 1
        # Algorithm derived from percentage method in https://files.nc.gov/ncdor/documents/files/nc-30_book_web.pdf

        wh = -round(((salary - (PST + (allowance_multiplier * allowances))) * 0.05599) + additional_wh)

        employee = self._createEmployee()
        employee.company_id.nc_unemp_rate_2018 = 0.06

        contract = self._createContract(employee,
                                        salary,
                                        struct_id=self.ref('l10n_us_nc_hr_payroll.hr_payroll_salary_structure_us_nc_employee'),
                                        schedule_pay=schedule_pay)
        contract.w4_is_nonresident_alien = True
        contract.nc_nc4_additional_wh = additional_wh
        contract.nc_nc4_allowances = allowances

        self.assertEqual(contract.schedule_pay, 'weekly')
        self.assertEqual(contract.w4_is_nonresident_alien, True)

        # tax rates
        nc_unemp = contract.nc_unemp_rate(2018) / -100.0

        self._log('2018 North Carolina tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NC_UNEMP_WAGES'], salary)
        self.assertPayrollEqual(cats['NC_UNEMP'], cats['NC_UNEMP_WAGES'] * nc_unemp)
        self.assertPayrollEqual(cats['NC_INC_WITHHOLD'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_nc_unemp_wages = self.NC_UNEMP_MAX_WAGE - salary if (self.NC_UNEMP_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2018 North Carolina tax second payslip weekly:')
        payslip = self._createPayslip(employee, '2018-02-01', '2018-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NC_UNEMP_WAGES'], remaining_nc_unemp_wages)
        self.assertPayrollEqual(cats['NC_UNEMP'], remaining_nc_unemp_wages * nc_unemp)

    def test_underflow(self):
        salary = 150.0
        schedule_pay = 'weekly'
        # allowance_multiplier and Portion of Standard Deduction for weekly
        allowance_multiplier = 48.08
        PST = 168.27

        exemption = 1

        #  Withholding should be 0, since pay is so low it's less than PST.
        wh = 0.0

        employee = self._createEmployee()
        employee.company_id.nc_unemp_rate_2018 = 0.06

        contract = self._createContract(employee, salary, struct_id=self.ref(
            'l10n_us_nc_hr_payroll.hr_payroll_salary_structure_us_nc_employee'), schedule_pay=schedule_pay)
        contract.nc_nc4_allowances = exemption

        self.assertEqual(contract.schedule_pay, 'weekly')

        # tax rates
        nc_unemp = contract.nc_unemp_rate(2018) / -100.0

        self._log('2018 North Carolina tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NC_UNEMP_WAGES'], salary)
        self.assertPayrollEqual(cats['NC_UNEMP'], cats['NC_UNEMP_WAGES'] * nc_unemp)
        self.assertPayrollEqual(cats['NC_INC_WITHHOLD'], wh)

        process_payslip(payslip)
