
from datetime import date
from .common import TestUsPayslip


class TestUsMoPayslip(TestUsPayslip):
    # Calculations from http://dor.mo.gov/forms/4282_2020.pdf
    MO_UNEMP_MAX_WAGE = 11500.0
    MO_UNEMP = 2.376

    TAX = [
        (1073.0, 1.5),
        (1073.0, 2.0),
        (1073.0, 2.5),
        (1073.0, 3.0),
        (1073.0, 3.5),
        (1073.0, 4.0),
        (1073.0, 4.5),
        (1073.0, 5.0),
        ( 'inf', 5.4),
    ]
    STD_DED = {
        '':                       0.0,  # Exempt
        'single':             12400.0,
        'married':            24800.0,
        'head_of_household':  18650.0,
    }

    def _test_sit(self, filing_status, schedule_pay):
        wage = 5000.0
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state('MO'),
                                        mo_mow4_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=0.0,
                                        schedule_pay=schedule_pay)

        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        pp = payslip.get_pay_periods_in_year()
        gross_salary = wage * pp
        standard_deduction = self.STD_DED[filing_status]

        mo_taxable_income = gross_salary - standard_deduction
        self._log('%s = %s - %s -' % (mo_taxable_income, gross_salary, standard_deduction))

        remaining_taxable_income = mo_taxable_income
        tax = 0.0
        for amt, rate in self.TAX:
            amt = float(amt)
            rate = rate / 100.0
            self._log(str(amt) + ' : ' + str(rate) + ' : ' + str(remaining_taxable_income))
            if (remaining_taxable_income - amt) > 0.0 or (remaining_taxable_income - amt) == 0.0:
                tax += rate * amt
            else:
                tax += rate * remaining_taxable_income
                break
            remaining_taxable_income = remaining_taxable_income - amt

        tax = -tax
        self._log('Computed annual tax: ' + str(tax))

        tax = tax / pp
        tax = round(tax)
        self._log('Computed period tax: ' + str(tax))
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), tax if filing_status else 0.0)

        contract.us_payroll_config_id.state_income_tax_additional_withholding = 100.0
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), (tax - 100.0) if filing_status else 0.0)

        contract.us_payroll_config_id.mo_mow4_sit_withholding = 200.0
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), -200.0 if filing_status else 0.0)

    def test_2020_taxes_single(self):
        self._test_er_suta('MO', self.MO_UNEMP, date(2020, 1, 1), wage_base=self.MO_UNEMP_MAX_WAGE)
        self._test_sit('single', 'weekly')

    def test_2020_spouse_not_employed(self):
        self._test_sit('married', 'semi-monthly')

    def test_2020_head_of_household(self):
        self._test_sit('head_of_household', 'monthly')

    def test_2020_underflow(self):
        # Payroll Period Weekly
        salary = 200.0

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MO'))

        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_SIT'], 0.0)
