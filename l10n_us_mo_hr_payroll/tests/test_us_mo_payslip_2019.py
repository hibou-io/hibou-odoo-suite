from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip


class TestUsMoPayslip(TestUsPayslip):
    # Calculations from http://dor.mo.gov/forms/4282_2019.pdf
    SALARY = 5000.0
    MO_ALLOWANCES = 3  # Different calculated amounts for different filing statuses
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
        standard_deduction = 6100.0
        mo_allowance_calculated = 0.0

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, struct_id=self.ref('l10n_us_mo_hr_payroll.hr_payroll_salary_structure_us_mo_employee'))
        contract.mo_mow4_spouse_employed = spouse_employed
        contract.mo_mow4_filing_status = 'single'
        contract.mo_mow4_exemptions = 3
        contract.mo_mow4_additional_withholding = 0.0

        self._log('2019 Missouri tax single first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_MO_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_MO_UNEMP'], cats['WAGE_US_MO_UNEMP'] * self.MO_UNEMP)

        mo_taxable_income = gross_salary - standard_deduction - mo_allowance_calculated
        self._log('%s = %s - %s - %s' % (mo_taxable_income, gross_salary, standard_deduction, mo_allowance_calculated))

        remaining_taxable_income = mo_taxable_income
        tax = 0.0
        for amt, rate in self.TAX:
            rate = rate / 100.0
            self._log(str(amt) + ' : ' + str(rate) + ' : ' + str(remaining_taxable_income))
            remaining_taxable_income = remaining_taxable_income - amt
            if remaining_taxable_income > 0.0 or remaining_taxable_income == 0.0:
                tax += rate * amt
            else:
                tax += rate * (remaining_taxable_income + amt)
                break
        tax = -tax
        self._log('Computed annual tax: ' + str(tax))

        tax = tax / pp
        tax = round(tax)
        self._log('Computed period tax: ' + str(tax))
        self.assertPayrollEqual(cats['EE_US_MO_INC_WITHHOLD'], tax)

    def test_2019_spouse_not_employed(self):
        # Payroll Period Semi-monthly
        salary = self.SALARY
        pp = 24.0
        gross_salary = salary * pp
        spouse_employed = False

        # Single
        standard_deduction = 12200.0
        mo_allowance_calculated = 0.0

        employee = self._createEmployee()

        contract = self._createContract(employee, salary,
                                        struct_id=self.ref('l10n_us_mo_hr_payroll.hr_payroll_salary_structure_us_mo_employee'),
                                        schedule_pay='semi-monthly')
        contract.mo_mow4_spouse_employed = spouse_employed
        contract.mo_mow4_filing_status = 'married'
        contract.mo_mow4_exemptions = 3
        contract.mo_mow4_additional_withholding = 0.0

        self._log('2019 Missouri tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        mo_taxable_income = gross_salary - standard_deduction - mo_allowance_calculated
        self._log(mo_taxable_income)

        remaining_taxable_income = mo_taxable_income
        tax = 0.0
        for amt, rate in self.TAX:
            rate = rate / 100.0
            self._log(str(amt) + ' : ' + str(rate) + ' : ' + str(remaining_taxable_income))
            remaining_taxable_income = remaining_taxable_income - amt
            if remaining_taxable_income > 0.0 or remaining_taxable_income == 0.0:
                tax += rate * amt
            else:
                tax += rate * (remaining_taxable_income + amt)
                break
        tax = -tax
        self._log('Computed annual tax: ' + str(tax))

        tax = tax / pp
        tax = round(tax)
        self._log('Computed period tax: ' + str(tax))
        self.assertPayrollEqual(cats['EE_US_MO_INC_WITHHOLD'], tax)

    def test_2019_head_of_household(self):
        # Payroll Period Weekly
        salary = self.SALARY

        # Payroll Period Weekly
        salary = self.SALARY
        pp = 52.0
        gross_salary = salary * pp
        spouse_employed = False

        # Single HoH
        standard_deduction = 18350.0 / 2.0
        mo_allowance_calculated = 0.0  # 2019 Allowances are no longer in the Missouri Withholding tables.

        employee = self._createEmployee()

        contract = self._createContract(employee, salary,
                                        struct_id=self.ref('l10n_us_mo_hr_payroll.hr_payroll_salary_structure_us_mo_employee'),
                                        schedule_pay='weekly')
        contract.mo_mow4_spouse_employed = spouse_employed
        contract.mo_mow4_filing_status = 'head_of_household'
        contract.mo_mow4_exemptions = 3
        contract.mo_mow4_additional_withholding = 0.0

        self._log('2019 Missouri tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        mo_taxable_income = gross_salary - standard_deduction - mo_allowance_calculated
        self._log(mo_taxable_income)

        remaining_taxable_income = mo_taxable_income
        tax = 0.0
        for amt, rate in self.TAX:
            rate = rate / 100.0
            self._log(str(amt) + ' : ' + str(rate) + ' : ' + str(remaining_taxable_income))
            remaining_taxable_income = remaining_taxable_income - amt
            if remaining_taxable_income > 0.0 or remaining_taxable_income == 0.0:
                tax += rate * amt
            else:
                tax += rate * (remaining_taxable_income + amt)
                break
        tax = -tax
        self._log('Computed annual tax: ' + str(tax))

        tax = tax / pp
        tax = round(tax)
        self._log('Computed period tax: ' + str(tax))
        self.assertPayrollEqual(cats['EE_US_MO_INC_WITHHOLD'], tax)

    def test_2019_underflow(self):
        # Payroll Period Weekly
        salary = 200.0

        employee = self._createEmployee()

        contract = self._createContract(employee, salary,
                                        struct_id=self.ref('l10n_us_mo_hr_payroll.hr_payroll_salary_structure_us_mo_employee'))

        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_MO_INC_WITHHOLD'], 0.0)
