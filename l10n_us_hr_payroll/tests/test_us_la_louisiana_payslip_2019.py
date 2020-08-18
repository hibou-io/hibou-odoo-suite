# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip


class TestUsLAPayslip(TestUsPayslip):

    # TAXES AND RATES
    LA_UNEMP_MAX_WAGE = 7700.00
    LA_UNEMP = -(1.14 / 100.0)

    def test_taxes_single_weekly(self):
        salary = 700.00
        schedule_pay = 'weekly'
        filing_status = 'single'
        exemptions = 1
        dependents = 2
        additional_withholding = 0
        # SEE http://revenue.louisiana.gov/TaxForms/1306(1_12)TF.pdf for example calculations
        # wh_to test is 19.42
        # Our algorithm correctly rounds whereas theirs does it prematurely.
        wh_to_check = -19.43
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('LA'),
                                        la_l4_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        la_l4_sit_exemptions=exemptions,
                                        la_l4_sit_dependents=dependents,
                                        schedule_pay=schedule_pay)

        self._log('2019 Louisiana tax first payslip weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.LA_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh_to_check)

        process_payslip(payslip)

        remaining_la_unemp_wages = self.LA_UNEMP_MAX_WAGE - salary if (self.LA_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2019 Louisiana tax second payslip weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_la_unemp_wages * self.LA_UNEMP)

    def test_taxes_married_biweekly(self):
        salary = 4600.00
        schedule_pay = 'bi-weekly'
        filing_status = 'married'
        exemptions = 2
        dependents = 3
        additional_withholding = 0
        # SEE http://revenue.louisiana.gov/TaxForms/1306(1_12)TF.pdf for example calculations
        # wh_to test is 157.12
        wh_to_check = -157.12
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('LA'),
                                        la_l4_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=additional_withholding,
                                        la_l4_sit_exemptions=exemptions,
                                        la_l4_sit_dependents=dependents,
                                        schedule_pay=schedule_pay)

        self._log('2019 Louisiana tax first payslip bi-weekly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.LA_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh_to_check)

        process_payslip(payslip)

        remaining_la_unemp_wages = self.LA_UNEMP_MAX_WAGE - salary if (self.LA_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2019 Louisiana tax second payslip bi-weekly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_la_unemp_wages * self.LA_UNEMP)
