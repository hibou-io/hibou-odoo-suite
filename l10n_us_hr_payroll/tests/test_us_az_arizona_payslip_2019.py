# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip


class TestUsAZPayslip(TestUsPayslip):

    # TAXES AND RATES
    AZ_UNEMP_MAX_WAGE = 7000.00
    AZ_UNEMP = -(2.00 / 100.0)

    def test_taxes_with_additional_wh(self):
        salary = 15000.00
        schedule_pay = 'weekly'
        withholding_percentage = 5.1
        percent_wh = (5.10 / 100)  # 5.1%
        additional_wh = 12.50

        wh_to_test = -((percent_wh * salary) + additional_wh)

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('AZ'),
                                        state_income_tax_additional_withholding=12.50,
                                        az_a4_sit_withholding_percentage=withholding_percentage,
                                        schedule_pay=schedule_pay)

        self._log('2019 Arizona tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], self.AZ_UNEMP_MAX_WAGE * self.AZ_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh_to_test)

        process_payslip(payslip)

        remaining_AZ_UNEMP_wages = 0.0  # We already reached max unemployment wages.

        self._log('2019 Arizona tax second payslip weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_AZ_UNEMP_wages * self.AZ_UNEMP)

    def test_taxes_monthly(self):
        salary = 1000.00
        schedule_pay = 'monthly'
        withholding_percentage = 2.7
        percent_wh = (2.70 / 100)  # 2.7%
        additional_wh = 0.0
        wh_to_test = -((percent_wh * salary) + additional_wh)

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('AZ'),
                                        state_income_tax_additional_withholding=0.0,
                                        az_a4_sit_withholding_percentage=withholding_percentage,
                                        schedule_pay=schedule_pay)

        self._log('2019 Arizona tax first payslip monthly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.AZ_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh_to_test)

        process_payslip(payslip)
