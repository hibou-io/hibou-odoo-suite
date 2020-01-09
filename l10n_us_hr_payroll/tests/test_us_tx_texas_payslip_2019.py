# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip
from odoo.addons.l10n_us_hr_payroll.models.hr_contract import USHRContract

class TestUsTXPayslip(TestUsPayslip):
    ###
    #   2019 Taxes and Rates
    ###
    TX_UNEMP_MAX_WAGE = 9000.0
    TX_UNEMP = -2.7 / 100.0
    TX_OA = 0.0
    TX_ETIA = -0.1 / 100.0

    def test_2019_taxes(self):
        salary = 5000.0

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('TX'),
                                        )

        self._log('2019 Texas tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)

        self.assertPayrollEqual(rules['ER_US_TX_SUTA'], salary * self.TX_UNEMP)
        self.assertPayrollEqual(rules['ER_US_TX_SUTA_OA'], salary * self.TX_OA)
        self.assertPayrollEqual(rules['ER_US_TX_SUTA_ETIA'], salary * self.TX_ETIA)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_tx_unemp_wages = self.TX_UNEMP_MAX_WAGE - salary if (self.TX_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2019 Texas tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)

        self.assertPayrollEqual(rules['ER_US_TX_SUTA'], remaining_tx_unemp_wages * self.TX_UNEMP)

    def test_2019_taxes_with_external(self):
        salary = 5000.0
        external_wages = 6000.0

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('TX'),
                                        external_wages=external_wages,
                                        )

        self._log('2019 Texas_external tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)

        expected_wage = self.TX_UNEMP_MAX_WAGE - external_wages
        self.assertPayrollEqual(rules['ER_US_TX_SUTA'], expected_wage * self.TX_UNEMP)
        self.assertPayrollEqual(rules['ER_US_TX_SUTA_OA'], expected_wage * self.TX_OA)
        self.assertPayrollEqual(rules['ER_US_TX_SUTA_ETIA'], expected_wage * self.TX_ETIA)

    def test_2019_taxes_with_state_exempt(self):
        salary = 5000.0
        external_wages = 6000.0

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('TX'),
                                        external_wages=external_wages,
                                        futa_type=USHRContract.FUTA_TYPE_BASIC)

        self._log('2019 Texas_external tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)

        self.assertPayrollEqual(rules.get('ER_US_TX_SUTA', 0.0), 0.0)
        self.assertPayrollEqual(rules.get('ER_US_TX_SUTA_OA', 0.0), 0.0)
        self.assertPayrollEqual(rules.get('ER_US_TX_SUTA_ETIA', 0.0), 0.0)
