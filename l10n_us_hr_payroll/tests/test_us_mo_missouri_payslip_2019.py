
from datetime import date
from .common import TestUsPayslip


class TestUsMoPayslip(TestUsPayslip):
    # Calculations from http://dor.mo.gov/forms/4282_2019.pdf
    SALARY = 12000.0
    MO_UNEMP = -2.376 / 100.0

    TAX = [
        (1053.0, 1.5),
        (1053.0, 2.0),
        (1053.0, 2.5),
        (1053.0, 3.0),
        (1053.0, 3.5),
        (1053.0, 4.0),
        (1053.0, 4.5),
        (1053.0, 5.0),
        (999999999.0, 5.4),
    ]

    def test_2019_taxes_single(self):
        # Payroll Period Monthly
        salary = self.SALARY
        pp = 12.0
        gross_salary = salary * pp
        spouse_employed = False

        # Single
        standard_deduction = 12400.0

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MO'),
                                        mo_mow4_sit_filing_status='single',
                                        state_income_tax_additional_withholding=0.0,
                                        schedule_pay='monthly')

        self._log('2019 Missouri tax single first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.MO_UNEMP)

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
        self.assertPayrollEqual(cats['EE_US_SIT'], tax)

    def test_2019_spouse_not_employed(self):
        # Payroll Period Semi-monthly
        salary = self.SALARY
        pp = 24.0
        gross_salary = salary * pp

        # Married
        standard_deduction = 24800.0

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MO'),
                                        mo_mow4_sit_filing_status='married',
                                        state_income_tax_additional_withholding=0.0,
                                        schedule_pay='semi-monthly')

        self._log('2019 Missouri tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        mo_taxable_income = gross_salary - standard_deduction
        self._log(mo_taxable_income)

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
        self.assertPayrollEqual(cats['EE_US_SIT'], tax)

    def test_2019_head_of_household(self):
        # Payroll Period Weekly
        salary = self.SALARY

        # Payroll Period Weekly
        salary = self.SALARY
        pp = 52.0
        gross_salary = salary * pp

        # Single HoH
        standard_deduction = 18650.0

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MO'),
                                        mo_mow4_sit_filing_status='head_of_household',
                                        state_income_tax_additional_withholding=0.0,
                                        schedule_pay='weekly')

        self._log('2019 Missouri tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        mo_taxable_income = gross_salary - standard_deduction
        self._log(mo_taxable_income)

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
        self.assertPayrollEqual(cats['EE_US_SIT'], tax)

    def test_2019_underflow(self):
        # Payroll Period Weekly
        salary = 200.0

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('MO'))

        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_SIT'], 0.0)
