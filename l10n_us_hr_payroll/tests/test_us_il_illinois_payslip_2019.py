# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip


class TestUsILPayslip(TestUsPayslip):
    # TAXES AND RATES
    IL_UNEMP_MAX_WAGE = 12960.00
    IL_UNEMP = -(3.175 / 100.0)

    def test_taxes_monthly(self):
        salary = 15000.00
        schedule_pay = 'monthly'
        basic_allowances = 1
        additional_allowances = 1
        flat_rate = (4.95 / 100)
        wh_to_test = -(flat_rate * (salary - ((basic_allowances * 2275 + additional_allowances * 1000) / 12.0)))

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('IL'),
                                        state_income_tax_additional_withholding=0.0,
                                        il_w4_sit_basic_allowances=1.0,
                                        il_w4_sit_additional_allowances=1.0,
                                        schedule_pay='monthly')

        self._log('2019 Illinois tax first payslip monthly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], self.IL_UNEMP_MAX_WAGE * self.IL_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh_to_test)

        process_payslip(payslip)

        remaining_IL_UNEMP_wages = 0.0  # We already reached max unemployment wages.

        self._log('2019 Illinois tax second payslip monthly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_IL_UNEMP_wages * self.IL_UNEMP)

    def test_taxes_with_additional_wh(self):
        salary = 15000.00
        schedule_pay = 'monthly'
        basic_allowances = 1
        additional_allowances = 1
        additional_wh = 15.0
        flat_rate = (4.95 / 100)
        wh_to_test = -(flat_rate * (salary - ((basic_allowances * 2275 + additional_allowances * 1000) / 12.0)) + additional_wh)

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('IL'),
                                        state_income_tax_additional_withholding=15.0,
                                        il_w4_sit_basic_allowances=1.0,
                                        il_w4_sit_additional_allowances=1.0,
                                        schedule_pay='monthly')

        self._log('2019 Illinois tax first payslip monthly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], self.IL_UNEMP_MAX_WAGE * self.IL_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh_to_test)
