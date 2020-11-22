# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip
from odoo.addons.l10n_us_hr_payroll.models.hr_contract import USHRContract


class TestUsOhPayslip(TestUsPayslip):
    ###
    #    Taxes and Rates
    ###
    OH_UNEMP_MAX_WAGE = 9500.0
    OH_UNEMP = -2.7 / 100.0

    def test_2019_taxes(self):
        salary = 5000.0

        # For formula here
        # http://www.tax.ohio.gov/Portals/0/employer_withholding/August2015Rates/WTH_OptionalComputerFormula_073015.pdf
        tw = salary * 12  # = 60000
        wd = ((tw - 40000) * 0.035 + 900) / 12 * 1.075

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('OH'),
                                        )

        self._log('2019 Ohio tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.OH_UNEMP)
        self.assertPayrollAlmostEqual(cats['EE_US_SIT'], -wd)  # Off by 0.6 cents so it rounds off by a penny
        #self.assertPayrollEqual(cats['EE_US_SIT'], -wd)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_oh_unemp_wages = self.OH_UNEMP_MAX_WAGE - salary if (self.OH_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2019 Ohio tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_oh_unemp_wages * self.OH_UNEMP)

    def test_2019_taxes_with_external(self):
        salary = 5000.0
        external_wages = 6000.0

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('OH'),
                                        external_wages=external_wages,
                                        )

        self._log('2019 Ohio_external tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], (self.OH_UNEMP_MAX_WAGE - external_wages) * self.OH_UNEMP)

    def test_2019_taxes_with_state_exempt(self):
        salary = 5000.0
        external_wages = 6000.0

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('OH'),
                                        external_wages=external_wages,
                                        futa_type=USHRContract.FUTA_TYPE_BASIC)

        self._log('2019 Ohio exempt tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        # FUTA_TYPE_BASIC
        self.assertPayrollEqual(cats.get('ER_US_SUTA', 0.0), salary * 0.0)
