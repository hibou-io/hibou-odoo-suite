# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip


class TestUsMtPayslip(TestUsPayslip):
    # Calculations from https://app.mt.gov/myrevenue/Endpoint/DownloadPdf?yearId=705
    MT_UNEMP = -1.18 / 100.0
    MT_UNEMP_AFT = -0.13 / 100.0

    def test_2019_taxes_one(self):
        # Payroll Period Semi-Monthly example
        salary = 550
        mt_mw4_exemptions = 5

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MT'),
                                        mt_mw4_sit_exemptions=mt_mw4_exemptions,
                                        schedule_pay='semi-monthly')

        self._log('2019 Montana tax single first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * (self.MT_UNEMP + self.MT_UNEMP_AFT))  # New non-combined...

        mt_taxable_income = salary - (79.0 * mt_mw4_exemptions)
        mt_withhold = round(0 + (0.018 * (mt_taxable_income - 0)))
        self.assertPayrollEqual(mt_taxable_income, 155.0)
        self.assertPayrollEqual(mt_withhold, 3.0)
        self.assertPayrollEqual(cats['EE_US_SIT'], -mt_withhold)

    def test_2019_taxes_two(self):
        # Payroll Period Bi-Weekly example
        salary = 2950
        mt_mw4_exemptions = 2

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MT'),
                                        mt_mw4_sit_exemptions=mt_mw4_exemptions,
                                        schedule_pay='bi-weekly')

        self._log('2019 Montana tax single first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], round(salary * (self.MT_UNEMP + self.MT_UNEMP_AFT), 2))

        # Note!!
        # The example calculation uses A = 16 but the actual table describes this as A = 18
        mt_taxable_income = salary - (73.0 * mt_mw4_exemptions)
        mt_withhold = round(18 + (0.06 * (mt_taxable_income - 577)))
        self.assertPayrollEqual(mt_taxable_income, 2804.0)
        self.assertPayrollEqual(mt_withhold, 152.0)
        self.assertPayrollEqual(cats['EE_US_SIT'], -mt_withhold)

    def test_2019_taxes_three(self):
        # Payroll Period Weekly example
        salary = 135
        mt_mw4_exemptions = 1

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MT'),
                                        mt_mw4_sit_exemptions=mt_mw4_exemptions,
                                        schedule_pay='weekly')

        self._log('2019 Montana tax single first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], round(salary * (self.MT_UNEMP + self.MT_UNEMP_AFT), 2))

        mt_taxable_income = salary - (37.0 * mt_mw4_exemptions)
        mt_withhold = round(0 + (0.018 * (mt_taxable_income - 0)))
        self.assertPayrollEqual(mt_taxable_income, 98.0)
        self.assertPayrollEqual(mt_withhold, 2.0)
        self.assertPayrollEqual(cats['EE_US_SIT'], -mt_withhold)

    def test_2019_taxes_three_exempt(self):
        # Payroll Period Weekly example
        salary = 135
        mt_mw4_exemptions = 1

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MT'),
                                        mt_mw4_sit_exemptions=mt_mw4_exemptions,
                                        mt_mw4_sit_exempt='reserve',
                                        schedule_pay='weekly')

        self._log('2019 Montana tax single first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), 0.0)

    def test_2019_taxes_three_additional(self):
        # Payroll Period Weekly example
        salary = 135
        mt_mw4_exemptions = 1
        mt_mw4_additional_withholding = 20.0

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MT'),
                                        mt_mw4_sit_exemptions=mt_mw4_exemptions,
                                        state_income_tax_additional_withholding=mt_mw4_additional_withholding,
                                        schedule_pay='weekly')

        self._log('2019 Montana tax single first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        mt_taxable_income = salary - (37.0 * mt_mw4_exemptions)
        mt_withhold = round(0 + (0.018 * (mt_taxable_income - 0)))
        self.assertPayrollEqual(mt_taxable_income, 98.0)
        self.assertPayrollEqual(mt_withhold, 2.0)
        self.assertPayrollEqual(cats['EE_US_SIT'], -mt_withhold + -mt_mw4_additional_withholding)
