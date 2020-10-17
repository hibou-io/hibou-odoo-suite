# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip


class TestUsHIPayslip(TestUsPayslip):

    # TAXES AND RATES
    HI_UNEMP_MAX_WAGE = 46800.00
    HI_UNEMP = -(2.40 / 100.0)

    def test_taxes_single_weekly(self):
        salary = 375.00
        schedule_pay = 'weekly'
        filing_status = 'single'
        allowances = 3
        wh_to_check = -15.3
        # Taxable income = (wage * payperiod ) - (allownaces * personal_exemption)
        # taxable_income = (375 * 52) - (3 * 1144) = 16068
        # Last = row[0] = 692
        # withholding = row[1] + ((row[2] / 100.0) * (taxable_income - last))
        # withholding = 682 + ((6.80 / 100.0 ) * (16068 - 14400)) = 795.42
        # wh_to_check = 795.42/52 = 15.3
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('HI'),
                                        hi_hw4_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=0.0,
                                        hi_hw4_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)

        self._log('2019 Hawaii tax first payslip single:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.HI_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh_to_check)

        process_payslip(payslip)

        remaining_id_unemp_wages = self.HI_UNEMP_MAX_WAGE - salary if (self.HI_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2019 Hawaii tax second payslip single:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_id_unemp_wages * self.HI_UNEMP)

    def test_taxes_married_monthly(self):
        salary = 5000.00
        schedule_pay = 'monthly'
        filing_status = 'married'
        allowances = 2
        wh_to_check = -287.1
        # Taxable income = (wage * payperiod ) - (allownaces * personal_exemption)
        # taxable_income = (5000 * 12) - (2 * 1144) = 57712
        # Last = row[0] = 48000
        # withholding = row[1] + ((row[2] / 100.0) * (taxable_income - last))
        # withholding = 2707 + ((7.70 / 100.0 ) * (57712 - 48000)) = 3445.112
        # wh_to_check = 3445.112/52 = 287.092
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('HI'),
                                        hi_hw4_sit_filing_status=filing_status,
                                        state_income_tax_additional_withholding=0.0,
                                        hi_hw4_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)

        self._log('2019 Hawaii tax first payslip monthly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.HI_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh_to_check)

        process_payslip(payslip)

        remaining_id_unemp_wages = self.HI_UNEMP_MAX_WAGE - salary if (self.HI_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2019 Hawaii tax second payslip monthly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_id_unemp_wages * self.HI_UNEMP)

