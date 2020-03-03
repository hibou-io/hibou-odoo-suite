# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip


class TestUsCAPayslip(TestUsPayslip):
    ###
    #    Taxes and Rates
    ###
    CA_MAX_WAGE = 7000
    CA_UIT = -3.5 / 100.0
    CA_ETT = -0.1 / 100.0
    CA_SDI = -1.0 / 100.0

    # Examples from https://www.edd.ca.gov/pdf_pub_ctr/20methb.pdf
    def test_example_a(self):
        salary = 210
        schedule_pay = 'weekly'
        allowances = 1
        additional_allowances = 0

        wh = 0.00

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('CA'),
                                        ca_de4_sit_filing_status='single',
                                        state_income_tax_additional_withholding=0.0,
                                        ca_de4_sit_allowances=allowances,
                                        ca_de4_sit_additional_allowances=additional_allowances,
                                        schedule_pay=schedule_pay)

        self._log('2019 California tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * (self.CA_UIT + self.CA_ETT))
        self.assertPayrollEqual(cats['EE_US_SUTA'], salary * self.CA_SDI)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)

    def test_example_b(self):
        salary = 1250
        schedule_pay = 'bi-weekly'
        allowances = 2
        additional_allowances = 1

        # Example B
        subject_to_withholding = salary - 38
        taxable_income = subject_to_withholding - 339
        computed_tax = (taxable_income - 632) * 0.022 + 6.95  # 6.95 Marginal Amount
        wh = computed_tax - 9.65  # two exemption allowances
        wh = -wh

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('CA'),
                                        ca_de4_sit_filing_status='married',
                                        state_income_tax_additional_withholding=0.0,
                                        ca_de4_sit_allowances=allowances,
                                        ca_de4_sit_additional_allowances=additional_allowances,
                                        schedule_pay=schedule_pay)

        self._log('2019 California tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * (self.CA_UIT + self.CA_ETT))
        self.assertPayrollEqual(cats['EE_US_SUTA'], salary * self.CA_SDI)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)


    def test_example_c(self):
        salary = 4100
        schedule_pay = 'monthly'
        allowances = 5
        additional_allowances = 0.0

        wh = -9.3

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('CA'),
                                        ca_de4_sit_filing_status='married',
                                        state_income_tax_additional_withholding=0.0,
                                        ca_de4_sit_allowances=allowances,
                                        ca_de4_sit_additional_allowances=additional_allowances,
                                        schedule_pay=schedule_pay)

        self._log('2019 California tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * (self.CA_UIT + self.CA_ETT))
        self.assertPayrollEqual(cats['EE_US_SUTA'], salary * self.CA_SDI)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_ca_uit_wages = self.CA_MAX_WAGE - salary if (self.CA_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2019 California tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], round((remaining_ca_uit_wages * (self.CA_UIT + self.CA_ETT)), 2))

    def test_example_d(self):
        salary = 800
        schedule_pay = 'weekly'
        allowances = 3
        additional_allowances = 0

        wh = -3.18

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('CA'),
                                        ca_de4_sit_filing_status='head_household',
                                        state_income_tax_additional_withholding=0.0,
                                        ca_de4_sit_allowances=allowances,
                                        ca_de4_sit_additional_allowances=additional_allowances,
                                        schedule_pay=schedule_pay)

        self._log('2019 California tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * (self.CA_UIT + self.CA_ETT))
        self.assertPayrollEqual(cats['EE_US_SUTA'], salary * self.CA_SDI)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_ca_uit_wages = self.CA_MAX_WAGE - salary if (self.CA_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2019 California tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], round((remaining_ca_uit_wages * (self.CA_UIT + self.CA_ETT)), 2))

    def test_example_e(self):
        salary = 1800
        schedule_pay = 'semi-monthly'
        allowances = 4
        additional_allowances = 0

        wh = -3.08

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('CA'),
                                        ca_de4_sit_filing_status='married',
                                        state_income_tax_additional_withholding=0.0,
                                        ca_de4_sit_allowances=allowances,
                                        ca_de4_sit_additional_allowances=additional_allowances,
                                        schedule_pay=schedule_pay)

        self._log('2019 California tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * (self.CA_UIT + self.CA_ETT))
        self.assertPayrollEqual(cats['EE_US_SUTA'], salary * self.CA_SDI)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_ca_uit_wages = self.CA_MAX_WAGE - salary if (self.CA_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2019 California tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], round((remaining_ca_uit_wages * (self.CA_UIT + self.CA_ETT)), 2))

    def test_example_f(self):
        salary = 45000
        schedule_pay = 'annually'
        allowances = 4
        additional_allowances = 0

        wh = -113.85

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('CA'),
                                        ca_de4_sit_filing_status='married',
                                        state_income_tax_additional_withholding=0.0,
                                        ca_de4_sit_allowances=allowances,
                                        ca_de4_sit_additional_allowances=additional_allowances,
                                        schedule_pay=schedule_pay)

        self._log('2019 California tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats['ER_US_SUTA'], self.CA_MAX_WAGE * (self.CA_UIT + self.CA_ETT))
        self.assertPayrollEqual(cats['EE_US_SUTA'], self.CA_MAX_WAGE * self.CA_SDI)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)