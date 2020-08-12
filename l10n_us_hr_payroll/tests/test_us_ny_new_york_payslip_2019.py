# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip


class TestUsNYPayslip(TestUsPayslip):
    ###
    #    Taxes and Rates
    ###
    NY_UNEMP_MAX_WAGE = 11400.0
    NY_UNEMP = 2.5
    NY_RSF = 0.075
    NY_MCTMT = 0.0

    def test_single_example1(self):
        salary = 400
        schedule_pay = 'weekly'
        allowances = 3
        additional_withholding = 0
        filing_status = 'single'
        additional = 0.0
        wh = -8.20

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('NY'),
                                        ny_it2104_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional,
                                        ny_it2104_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)

        self.assertEqual(contract.schedule_pay, 'weekly')
        self._log('2018 New York tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NY_UNEMP'], cats['NY_UNEMP_WAGES'] * self.NY_UNEMP)
        self.assertPayrollEqual(cats['NY_RSF'], cats['NY_UNEMP_WAGES'] * self.NY_RSF)
        self.assertPayrollEqual(cats['NY_MCTMT'], cats['NY_UNEMP_WAGES'] * self.NY_MCTMT)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)

    def test_married_example2(self):
        salary = 5000
        schedule_pay = 'semi-monthly'
        allowances = 3
        additional = 0
        filing_status = 'married'
        wh = -284.19

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('NY'),
                                        ny_it2104_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional,
                                        ny_it2104_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)

        self._log('2019 New York tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['NY_UNEMP'], cats['NY_UNEMP_WAGES'] * self.NY_UNEMP)
        self.assertPayrollEqual(cats['NY_RSF'], cats['NY_UNEMP_WAGES'] * self.NY_RSF)
        self.assertPayrollEqual(cats['NY_MCTMT'], cats['NY_UNEMP_WAGES'] * self.NY_MCTMT)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)

    def test_single_example3(self):
        salary = 50000
        schedule_pay = 'monthly'
        allowances = 3
        additional = 0
        filing_status = 'single'
        wh = -3575.63

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('NY'),
                                        ny_it2104_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional,
                                        ny_it2104_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)

        self._log('2019 New York tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

    def test_exempt_example3(self):
        salary = 50000
        schedule_pay = 'monthly'
        allowances = 3
        additional = 0
        filing_status = ''
        wh = 0.0

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('NY'),
                                        ny_it2104_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional,
                                        ny_it2104_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)

        self._log('2019 New York tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

