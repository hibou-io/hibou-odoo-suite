# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date
from .common import TestUsPayslip, process_payslip


class TestUsWYPayslip(TestUsPayslip):

    # TAXES AND RATES
    WY_UNEMP_MAX_WAGE = 25400
    WY_UNEMP = -2.10 / 100.0

    def test_2019_taxes(self):
        salary = 15000.00

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('WY'))

        self._log('2019 Wyoming tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.WY_UNEMP)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_wy_unemp_wages = self.WY_UNEMP_MAX_WAGE - salary if (self.WY_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2019 Wyoming tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_wy_unemp_wages * self.WY_UNEMP)

    def test_2019_taxes_with_external(self):
        # Wage is the cap itself, 25400
        # so salary is equal to self.WY_UNEMP
        salary = 25400

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('WY'))

        self._log('2019 Wyoming External tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.WY_UNEMP)
