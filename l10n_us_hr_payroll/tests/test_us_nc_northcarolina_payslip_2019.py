# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip


class TestUsNCPayslip(TestUsPayslip):
    ###
    #    Taxes and Rates
    ###
    NC_UNEMP_MAX_WAGE = 24300.0
    NC_UNEMP = -1.0 / 100.0
    NC_INC_TAX = -0.0535


    def test_2019_taxes_weekly(self):
        salary = 20000.0
        # allowance_multiplier and Portion of Standard Deduction for weekly
        allowance_multiplier = 48.08
        PST = 192.31
        exemption = 1
        # Algorithm derived from percentage method in https://files.nc.gov/ncdor/documents/files/nc-30_book_web.pdf
        wh = -round((salary - (PST + (allowance_multiplier * exemption))) * -self.NC_INC_TAX)

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('NC'),
                                        nc_nc4_sit_filing_status='married',
                                        state_income_tax_additional_withholding=0.0,
                                        nc_nc4_sit_allowances=1.0,
                                        schedule_pay='weekly')

        self._log('2019 North Carolina tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_NC_UNEMP_wages = self.NC_UNEMP_MAX_WAGE - salary if (self.NC_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary
        self._log('2019 North Carolina tax second payslip weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_NC_UNEMP_wages * self.NC_UNEMP)

    def test_2019_taxes_with_external_weekly(self):
        salary = 5000.0
        schedule_pay = 'weekly'

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('NC'),
                                        nc_nc4_sit_filing_status='married',
                                        state_income_tax_additional_withholding=0.0,
                                        nc_nc4_sit_allowances=1.0,
                                        schedule_pay='weekly')

        self._log('2019 NorthCarolina_external tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.NC_UNEMP)

    def test_2019_taxes_biweekly(self):
        salary = 5000.0
        schedule_pay = 'bi-weekly'
        # allowance_multiplier and Portion of Standard Deduction for weekly
        allowance_multiplier = 96.15
        PST = 384.62

        allowances = 2
        # Algorithm derived from percentage method in https://files.nc.gov/ncdor/documents/files/nc-30_book_web.pdf

        wh = -round((salary - (PST + (allowance_multiplier * allowances))) * -self.NC_INC_TAX)

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('NC'),
                                        nc_nc4_sit_filing_status='married',
                                        state_income_tax_additional_withholding=0.0,
                                        nc_nc4_sit_allowances=2.0,
                                        schedule_pay='bi-weekly')

        self._log('2019 North Carolina tax first payslip bi-weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.NC_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_NC_UNEMP_wages = self.NC_UNEMP_MAX_WAGE - salary if (self.NC_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2019 North Carolina tax second payslip bi-weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_NC_UNEMP_wages * self.NC_UNEMP)

    def test_2019_taxes_semimonthly(self):
        salary = 4000.0
        # allowance_multiplier and Portion of Standard Deduction for weekly
        allowance_multiplier = 104.17
        PST = 625.00

        allowances = 1
        # Algorithm derived from percentage method in https://files.nc.gov/ncdor/documents/files/nc-30_book_web.pdf

        wh = -round((salary - (PST + (allowance_multiplier * allowances))) * -self.NC_INC_TAX)

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('NC'),
                                        nc_nc4_sit_filing_status='head_household',
                                        state_income_tax_additional_withholding=0.0,
                                        nc_nc4_sit_allowances=1.0,
                                        schedule_pay='semi-monthly')

        self._log('2019 North Carolina tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.NC_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_NC_UNEMP_wages = self.NC_UNEMP_MAX_WAGE - salary if (self.NC_UNEMP_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2019 North Carolina tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_NC_UNEMP_wages * self.NC_UNEMP)

    def test_2019_taxes_monthly(self):
        salary = 4000.0
        schedule_pay = 'monthly'
        # allowance_multiplier and Portion of Standard Deduction for weekly
        allowance_multiplier = 208.33
        PST = 833.33

        allowances = 1
        # Algorithm derived from percentage method in https://files.nc.gov/ncdor/documents/files/nc-30_book_web.pdf

        wh = -round((salary - (PST + (allowance_multiplier * allowances))) * -self.NC_INC_TAX)

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('NC'),
                                        nc_nc4_sit_filing_status='single',
                                        state_income_tax_additional_withholding=0.0,
                                        nc_nc4_sit_allowances=1.0,
                                        schedule_pay='monthly')

        self._log('2019 North Carolina tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.NC_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_NC_UNEMP_wages = self.NC_UNEMP_MAX_WAGE - salary if (
                    self.NC_UNEMP_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2019 North Carolina tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_NC_UNEMP_wages * self.NC_UNEMP)

    def test_additional_withholding(self):
        salary = 4000.0
        # allowance_multiplier and Portion of Standard Deduction for weekly
        allowance_multiplier = 48.08
        PST = 192.31
        additional_wh = 40.0

        #4000 - (168.27 + (48.08 * 1)

        allowances = 1
        # Algorithm derived from percentage method in https://files.nc.gov/ncdor/documents/files/nc-30_book_web.pdf

        wh = -round(((salary - (PST + (allowance_multiplier * allowances))) * -self.NC_INC_TAX) + additional_wh)

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('NC'),
                                        nc_nc4_sit_filing_status='married',
                                        state_income_tax_additional_withholding=40.0,
                                        nc_nc4_sit_allowances=1.0,
                                        schedule_pay='weekly')

        self._log('2019 North Carolina tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_NC_UNEMP_wages = self.NC_UNEMP_MAX_WAGE - salary if (self.NC_UNEMP_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2019 North Carolina tax second payslip weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_NC_UNEMP_wages * self.NC_UNEMP)
