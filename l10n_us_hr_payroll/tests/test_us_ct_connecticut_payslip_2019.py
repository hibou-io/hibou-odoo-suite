# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip


class TestUsCTPayslip(TestUsPayslip):
    # TAXES AND RATES
    CT_UNEMP_MAX_WAGE = 15000.00
    CT_UNEMP = -(3.40 / 100.0)

    def test_taxes_weekly_with_additional_wh(self):

        # Tax tables can be found here:
        # https://portal.ct.gov/-/media/DRS/Publications/pubsip/2019/IP-2019(1).pdf?la=en
        # Step 1 - Wages per period -> 10000.00
        salary = 10000.00
        # Step 2 and 3 - Annual wages -> 10000.00 * 52.0 -> 520000.0
        schedule_pay = 'weekly'
        # Step 4 Employee Withholding Code -> A
        wh_code = 'a'
        # Step 5 - Use annual wages and withholding code with table for exemption amount.
        # exemption_amt = 0 since highest bracket.
        # Step 6 - Subtract 5 from 3 for taxable income.
        # taxable income = 520000.00 since we do not have an exemption.
        # Step 7 - Determine initial amount from table
        #  initial = 31550 + ((6.99 / 100) * (520000.00 - 500000.00))
        #  32948.0
        # Step 8 - Determine the tax rate phase out add back from table.
        #  phase_out = 200
        # Step 9 - Determine the recapture amount from table.
        # Close to top, but not top. -> 2900
        # Step 10 - Add Step 7, 8, 9
        # 32948.0 + 200 + 2900.00 - > 36048.0
        # Step 11 - Determine decimal amount from personal tax credits.
        # We get no tax credit.
        # Step 12 - Multiple Step 10 by 1.00 - Step 11
        # 36048.0 * 1.00 = 36048.0
        # Step 13 - Divide by the number of pay periods.
        # 36048.0 / 52.0 = 693.23
        # Step 14 & 15 & 16- Add / Subtract the additional or under withholding amount. Then Add this to the amount
        # for withholding per period.
        additional_wh = 12.50
        # 693.23 + 12.50 ->
        wh = -705.73

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('CT'),
                                        ct_w4na_sit_code=wh_code,
                                        state_income_tax_additional_withholding=additional_wh,
                                        schedule_pay=schedule_pay)

        self._log('2019 Connecticut tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.CT_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        process_payslip(payslip)

        remaining_CT_UNEMP_wages = 5000.00  # We already reached the maximum wage for unemployment insurance.
        self._log('2019 Connecticut tax second payslip weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_CT_UNEMP_wages * self.CT_UNEMP)

    def test_taxes_weekly_with_different_code(self):

        # Tax tables can be found here:
        # https://portal.ct.gov/-/media/DRS/Publications/pubsip/2019/IP-2019(1).pdf?la=en
        # Step 1 - Wages per period -> 15000.00
        salary = 15000.00
        # Step 2 and 3 - Annual wages -> 15000.00 * 12.0 -> 180000.0
        schedule_pay = 'monthly'
        # Step 4 Employee Withholding Code -> B
        wh_code = 'b'
        # Step 5 - Use annual wages and withholding code with table for exemption amount.
        # exemption_amt = 0 since highest bracket.
        # Step 6 - Subtract 5 from 3 for taxable income.
        # taxable income = 180000.0 since we do not have an exemption.
        # Step 7 - Determine initial amount from table
        #  initial = 8080 + ((6.00 / 100) * (180000.0 - 160000))
        #  9280.0
        # Step 8 - Determine the tax rate phase out add back from table.
        #  phase_out = 320
        # Step 9 - Determine the recapture amount from table.
        # Bottom -> 0
        # Step 10 - Add Step 7, 8, 9
        # 9280.0 + 320 + 0 - > 9600.0
        # Step 11 - Determine decimal amount from personal tax credits.
        # We get no tax credit.
        # Step 12 - Multiple Step 10 by 1.00 - Step 11
        # 9600.0 * 1.00 = 9600.0
        # Step 13 - Divide by the number of pay periods.
        # 9600.0 / 12.0 = 800.0
        # Step 14 & 15 & 16- Add / Subtract the additional or under withholding amount. Then Add this to the amount
        # for withholding per period.
        additional_wh = 15.00
        # 800.0 + 15.00 ->
        wh = -815.0

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('CT'),
                                        ct_w4na_sit_code=wh_code,
                                        state_income_tax_additional_withholding=additional_wh,
                                        schedule_pay=schedule_pay)

        self._log('2019 Connecticut tax first payslip monthly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], self.CT_UNEMP_MAX_WAGE * self.CT_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)
