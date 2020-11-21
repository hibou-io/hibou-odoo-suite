# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip


class TestUsARPayslip(TestUsPayslip):
    # https://www.dfa.arkansas.gov/images/uploads/incomeTaxOffice/whformula.pdf Calculation based on this file.
    AR_UNEMP_MAX_WAGE = 10000.00
    AR_UNEMP = -3.2 / 100.0
    AR_INC_TAX = -0.0535

    def test_taxes_monthly(self):
        salary = 2127.0
        schedule_pay = 'monthly'

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('AR'),
                                        state_income_tax_additional_withholding=0.0,
                                        ar_ar4ec_sit_allowances=2.0,
                                        state_income_tax_exempt=False,
                                        schedule_pay='monthly')

        self._log('2019 Arkansas tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        # Not exempt from rule 1 or rule 2 - unemployment wages., and actual unemployment.
        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.AR_UNEMP)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums
        remaining_AR_UNEMP_wages = self.AR_UNEMP_MAX_WAGE - salary if (self.AR_UNEMP_MAX_WAGE - 2*salary < salary) else salary
        # We reached the cap of 10000.0 in the first payslip.
        self._log('2019 Arkansas tax second payslip weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_AR_UNEMP_wages * self.AR_UNEMP)

    def test_additional_withholding(self):
        salary = 5000.0
        schedule_pay = 'monthly'
        pay_periods = 12
        allowances = 2
        # TODO: comment on how it was calculated
        test_ar_amt = 2598.60

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('AR'),
                                        state_income_tax_additional_withholding=100.0,
                                        ar_ar4ec_sit_allowances=2.0,
                                        state_income_tax_exempt=False,
                                        schedule_pay='monthly')


        self._log('2019 Arkansas tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.AR_UNEMP)
        # TODO: change to hand the test_ar_amt already be divided by pay periods
        self.assertPayrollAlmostEqual(cats['EE_US_SIT'], -round(test_ar_amt / pay_periods) - 100)

        process_payslip(payslip)
