# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date
from .common import TestUsPayslip, process_payslip
from odoo.addons.l10n_us_hr_payroll.models.hr_contract import USHRContract


class TestUsVaPayslip(TestUsPayslip):
    ###
    #    Taxes and Rates
    ###
    VA_UNEMP_MAX_WAGE = 8000.0
    VA_UNEMP = 2.51
    VA_SIT_DEDUCTION = 4500.0
    VA_SIT_EXEMPTION = 930.0
    VA_SIT_OTHER_EXEMPTION = 800.0

    def test_2019_taxes(self):
        salary = 5000.0

        # For formula from https://www.tax.virginia.gov/withholding-calculator
        """
        Key
        G = Gross Pay for Pay Period	P = Pay periods per year
        A = Annualized gross pay	E1 = Personal and Dependent Exemptions
        T = Annualized taxable income	E2 = Age 65 and Over & Blind Exemptions
        WH = Tax to be withheld for pay period	W = Annualized tax to be withheld
        G x P - [$3000+ (E1 x 930) + (E2 x 800)] = T
        Calculate W as follows:
        If T is:	W is:
        Not over $3,000	2% of T
        Over	But Not Over	Then
        $3,000	$5,000	        $60 + (3% of excess over $3,000)
        $5,000	$17,000	        $120 + (5% of excess over $5,000)
        $17,000	 	            $720 + (5.75% of excess over $17,000)
        W / P = WH
        """
        e1 = 2
        e2 = 0
        t = salary * 12 - (self.VA_SIT_DEDUCTION + (e1 * self.VA_SIT_EXEMPTION) + (e2 * self.VA_SIT_OTHER_EXEMPTION))

        if t <= 3000:
            w = 0.02 * t
        elif t <= 5000:
            w = 60 + (0.03 * (t - 3000))
        elif t <= 17000:
            w = 120 + (0.05 * (t - 5000))
        else:
            w = 720 + (0.0575 * (t - 17000))

        wh = w / 12

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('VA'),
                                        va_va4_sit_exemptions=e1,
                                        va_va4_sit_other_exemptions=e2
                                        )

        # tax rates
        va_unemp = self.VA_UNEMP / -100.0

        self._log('2019 Virginia tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * va_unemp)
        self.assertPayrollEqual(cats['EE_US_SIT'], -wh)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_va_unemp_wages = self.VA_UNEMP_MAX_WAGE - salary if (self.VA_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2019 Virginia tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_va_unemp_wages * va_unemp)

    def test_2019_taxes_with_external(self):
        salary = 5000.0
        external_wages = 6000.0

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('VA'),
                                        external_wages=external_wages,
                                        )

        # tax rates
        va_unemp = self.VA_UNEMP / -100.0

        self._log('2019 Virginia_external tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats['ER_US_SUTA'], (self.VA_UNEMP_MAX_WAGE - external_wages) * va_unemp)

    def test_2019_taxes_with_state_exempt(self):
        salary = 5000.0
        external_wages = 6000.0

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('VA'),
                                        external_wages=external_wages,
                                        futa_type=USHRContract.FUTA_TYPE_BASIC)

        # tax rates
        self._log('2019 Virginia exempt tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], 0.0)
