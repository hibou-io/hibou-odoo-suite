# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip


class TestUsMIPayslip(TestUsPayslip):
    # Taxes and Rates
    MI_UNEMP_MAX_WAGE = 9500.0
    MI_UNEMP = - 2.7 / 100.0
    MI_INC_TAX = - 4.25 / 100.0
    ANNUAL_EXEMPTION_AMOUNT = 4400.00
    PAY_PERIOD_DIVISOR = {
        'weekly': 52.0,
        'bi-weekly': 26.0,
        'semi-monthly': 24.0,
        'monthly': 12.0
    }

    def test_2019_taxes_weekly(self):
        salary = 5000.0
        schedule_pay = 'weekly'
        exemptions = 1

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MI'),
                                        state_income_tax_additional_withholding=0.0,
                                        mi_w4_sit_exemptions=1.0,
                                        schedule_pay='weekly')

        allowance_amount = self.ANNUAL_EXEMPTION_AMOUNT / self.PAY_PERIOD_DIVISOR[schedule_pay]
        wh = -((salary - (allowance_amount * exemptions)) * -self.MI_INC_TAX)

        self._log('2019 Michigan tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.MI_UNEMP)
        self.assertPayrollAlmostEqual(cats['EE_US_SIT'], wh)
    #
        process_payslip(payslip)

        # Make a new payslip, this one will have maximums
        remaining_MI_UNEMP_wages = self.MI_UNEMP_MAX_WAGE - salary if (self.MI_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2019 Michigan tax second payslip weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_MI_UNEMP_wages * self.MI_UNEMP)

    def test_2019_taxes_biweekly(self):
        salary = 5000.0
        schedule_pay = 'bi-weekly'
        allowance_amount = self.ANNUAL_EXEMPTION_AMOUNT / self.PAY_PERIOD_DIVISOR[schedule_pay]
        exemption = 2

        wh = -((salary - (allowance_amount * exemption)) * -self.MI_INC_TAX)

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MI'),
                                        state_income_tax_additional_withholding=0.0,
                                        mi_w4_sit_exemptions=2.0,
                                        schedule_pay='bi-weekly')

        self._log('2019 Michigan tax first payslip bi-weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.MI_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums
        remaining_MI_UNEMP_wages = self.MI_UNEMP_MAX_WAGE - salary if (self.MI_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2019 Michigan tax second payslip bi-weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_MI_UNEMP_wages * self.MI_UNEMP)

    def test_2019_taxes_semimonthly(self):
        salary = 5000.0
        schedule_pay = 'semi-monthly'
        allowance_amount = self.ANNUAL_EXEMPTION_AMOUNT / self.PAY_PERIOD_DIVISOR[schedule_pay]
        exemption = 1

        wh = -((salary - (allowance_amount * exemption)) * -self.MI_INC_TAX)

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MI'),
                                        state_income_tax_additional_withholding=0.0,
                                        mi_w4_sit_exemptions=1.0,
                                        schedule_pay='semi-monthly')

        self._log('2019 Michigan tax first payslip semi-monthly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.MI_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums
        remaining_MI_UNEMP_wages = self.MI_UNEMP_MAX_WAGE - salary if (self.MI_UNEMP_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2019 Michigan tax second payslip semi-monthly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_MI_UNEMP_wages * self.MI_UNEMP)

    def test_2019_taxes_monthly(self):
        salary = 5000.0
        schedule_pay = 'monthly'
        allowance_amount = self.ANNUAL_EXEMPTION_AMOUNT / self.PAY_PERIOD_DIVISOR[schedule_pay]
        exemption = 1

        wh = -((salary - (allowance_amount * exemption)) * -self.MI_INC_TAX)

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MI'),
                                        state_income_tax_additional_withholding=0.0,
                                        mi_w4_sit_exemptions=1.0,
                                        schedule_pay='monthly')

        self._log('2019 Michigan tax first payslip monthly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.MI_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums
        remaining_MI_UNEMP_wages = self.MI_UNEMP_MAX_WAGE - salary if (
                    self.MI_UNEMP_MAX_WAGE - (2 * salary) < salary) \
            else salary

        self._log('2019 Michigan tax second payslip monthly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_MI_UNEMP_wages * self.MI_UNEMP)

    def test_additional_withholding(self):
        salary = 5000.0
        schedule_pay = 'weekly'
        allowance_amount = 0.0
        allowance_amount = self.ANNUAL_EXEMPTION_AMOUNT / self.PAY_PERIOD_DIVISOR[schedule_pay]
        additional_wh = 40.0
        exemption = 1

        wh = -(((salary - (allowance_amount * exemption)) * -self.MI_INC_TAX) + additional_wh)

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MI'),
                                        state_income_tax_additional_withholding=40.0,
                                        mi_w4_sit_exemptions=1.0,
                                        schedule_pay='weekly')

        self._log('2019 Michigan tax first payslip with additional withholding:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.MI_UNEMP)
        self.assertPayrollAlmostEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)
