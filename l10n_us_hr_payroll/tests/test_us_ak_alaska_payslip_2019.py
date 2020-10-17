# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip


class TestUsAKPayslip(TestUsPayslip):
    # TAXES AND RATES
    AK_UNEMP_MAX_WAGE = 39900.00
    AK_UNEMP = -(1.780 / 100.0)
    AK_UNEMP_EE = -(0.5 / 100.0)

    def test_taxes_monthly_over_max(self):
        salary = 50000.00
        schedule_pay = 'monthly'

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('AK'),
                                        state_income_tax_additional_withholding=0.0,
                                        schedule_pay=schedule_pay)

        self._log('2019 Alaska tax first payslip monthly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], self.AK_UNEMP_MAX_WAGE * self.AK_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SUTA'], self.AK_UNEMP_MAX_WAGE * self.AK_UNEMP_EE)

        process_payslip(payslip)

        remaining_ak_unemp_wages = 0.00  # We already reached the maximum wage for unemployment insurance.

        self._log('2019 Alaska tax second payslip monthly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_ak_unemp_wages * self.AK_UNEMP)  # 0

    def test_taxes_weekly_under_max(self):
        salary = 5000.00
        schedule_pay = 'weekly'

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('AK'),
                                        state_income_tax_additional_withholding=0.0,
                                        schedule_pay=schedule_pay)

        self._log('2019 Alaska tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.AK_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SUTA'], salary * self.AK_UNEMP_EE)

        process_payslip(payslip)
