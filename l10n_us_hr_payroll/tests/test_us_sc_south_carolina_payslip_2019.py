# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip


class TestUsSCPayslip(TestUsPayslip):

    #    Taxes and Rates
    SC_UNEMP_MAX_WAGE = 14000.0
    US_SC_UNEMP = -1.09 / 100
    US_SC_exemption_amount = 2510.00

    def test_2019_taxes_weekly(self):
        # We will hand calculate the amount to test for state withholding.
        schedule_pay = 'weekly'
        salary = 50000.00  # Employee is paid 50000 per week to be in top tax bracket
        allowances = 2
        # Calculate annual wages
        annual = 50000 * 52.0
        # From our annual we deduct personal exemption amounts.
        # We deduct 2510.00 per exemption. Since we have two exemptions:
        personal_exemption = self.US_SC_exemption_amount * allowances  # 5020.0
        # From annual, we will also deduct a standard_deduction of  3470.00 or .1 of salary, which ever
        # is small -> if 1 or more exemptions, else 0
        standard_deduction = 3470.00
        taxable_income = annual - personal_exemption - standard_deduction  # 2591510.0
        # We then calculate the amounts off the SC tax pdf tables.
        # 2591478.0 is in the highest bracket
        test_amt = (taxable_income * (7.0 / 100.0)) - 467.95
        test_amt = 180935.51
        # Make it per period then negative
        test_amt = (test_amt / 52.0)  # Divided by 52 since it is weekly.
        # test_amt = 3479.52
        test_amt = -test_amt

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('SC'),
                                        state_income_tax_exempt=False,
                                        sc_w4_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)

        self._log('2019 South Carolina tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollAlmostEqual(cats['ER_US_SUTA'], self.SC_UNEMP_MAX_WAGE * self.US_SC_UNEMP)
        self.assertPayrollAlmostEqual(cats['EE_US_SIT'], test_amt)

        process_payslip(payslip)

        remaining_SC_UNEMP_wages = self.SC_UNEMP_MAX_WAGE - annual if (annual < self.SC_UNEMP_MAX_WAGE) \
            else 0.00

        self._log('2019 South Carolina tax second payslip:')

        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertEqual(0.0, remaining_SC_UNEMP_wages)
        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_SC_UNEMP_wages * self.US_SC_UNEMP)

    def test_2019_taxes_filing_status(self):
        salary = 20000.00  # Wages per pay period
        schedule_pay = 'monthly'
        annual = salary * 12
        allowances = 1
        # Hand Calculations
        personal_exemption = 2510.00
        standard_deduction = min(3470.00, .1 * annual)  # 3470.0 but min is shown for the process
        taxable = annual - personal_exemption - standard_deduction
        # taxable = 234020
        test_amt = ((taxable) * (7.0 / 100.0)) - 467.95  # 15991.850000000002
        test_amt = test_amt / 12.0  # Put it into monthly -> 1332.654166666667
        # Make it negative
        test_amt = -test_amt

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('SC'),
                                        state_income_tax_exempt=False,
                                        sc_w4_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)

        self._log('2019 South Carolina tax first payslip: ')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], self.SC_UNEMP_MAX_WAGE * self.US_SC_UNEMP)
        self.assertPayrollAlmostEqual(cats['EE_US_SIT'], test_amt)

        process_payslip(payslip)
