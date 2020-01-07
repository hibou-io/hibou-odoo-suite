# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip
from odoo.addons.l10n_us_hr_payroll.models.hr_contract import USHRContract


class TestUsFlPayslip(TestUsPayslip):
    ###
    #   2019 Taxes and Rates
    ###
    FL_UNEMP_MAX_WAGE = 7000.0
    FL_UNEMP = -2.7 / 100.0

    def test_2019_taxes(self):
        salary = 5000.0

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('FL'))

        self._log('2019 Florida tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.FL_UNEMP)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_fl_unemp_wages = self.FL_UNEMP_MAX_WAGE - salary if (self.FL_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2019 Florida tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_fl_unemp_wages * self.FL_UNEMP)

    def test_2019_taxes_with_external(self):
        salary = 5000.0
        external_wages = 6000.0

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        external_wages=external_wages,
                                        state_id=self.get_us_state('FL'))

        self._log('2019 Forida_external tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], (self.FL_UNEMP_MAX_WAGE - external_wages) * self.FL_UNEMP)

    def test_2019_taxes_with_state_exempt(self):
        salary = 5000.0
        external_wages = 6000.0

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        external_wages=external_wages,
                                        futa_type=USHRContract.FUTA_TYPE_BASIC,
                                        state_id=self.get_us_state('FL'))

        self._log('2019 Forida_external tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats.get('ER_US_SUTA', 0.0), 0.0)
