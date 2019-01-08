from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip
from odoo.addons.l10n_us_hr_payroll.models.l10n_us_hr_payroll import USHrContract


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
        contract = self._createContract(employee, salary, struct_id=self.ref('l10n_us_tx_hr_payroll.hr_payroll_salary_structure_us_tx_employee'))

        self._log('2019 Texas tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_TX_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_TX_UNEMP'], cats['WAGE_US_TX_UNEMP'] * self.TX_UNEMP)
        self.assertPayrollEqual(cats['ER_US_TX_OA'], cats['WAGE_US_TX_UNEMP'] * self.TX_OA)
        self.assertPayrollEqual(cats['ER_US_TX_ETIA'], cats['WAGE_US_TX_UNEMP'] * self.TX_ETIA)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_tx_unemp_wages = self.TX_UNEMP_MAX_WAGE - salary if (self.TX_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2019 Texas tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_TX_UNEMP'], remaining_tx_unemp_wages)
        self.assertPayrollEqual(cats['ER_US_TX_UNEMP'], remaining_tx_unemp_wages * self.TX_UNEMP)

    def test_2019_taxes_with_external(self):
        salary = 5000.0
        external_wages = 6000.0

        employee = self._createEmployee()

        contract = self._createContract(employee, salary, external_wages=external_wages,
                                        struct_id=self.ref('l10n_us_tx_hr_payroll.hr_payroll_salary_structure_us_tx_employee'))

        self._log('2019 Texas_external tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_TX_UNEMP'], self.TX_UNEMP_MAX_WAGE - external_wages)
        self.assertPayrollEqual(cats['ER_US_TX_UNEMP'], cats['WAGE_US_TX_UNEMP'] * self.TX_UNEMP)
        self.assertPayrollEqual(cats['ER_US_TX_OA'], cats['WAGE_US_TX_UNEMP'] * self.TX_OA)
        self.assertPayrollEqual(cats['ER_US_TX_ETIA'], cats['WAGE_US_TX_UNEMP'] * self.TX_ETIA)

    def test_2019_taxes_with_state_exempt(self):
        salary = 5000.0
        external_wages = 6000.0

        employee = self._createEmployee()

        contract = self._createContract(employee, salary, external_wages=external_wages, struct_id=self.ref(
            'l10n_us_tx_hr_payroll.hr_payroll_salary_structure_us_tx_employee'), futa_type=USHrContract.FUTA_TYPE_BASIC)

        self._log('2019 Texas_external tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats.get('WAGE_US_TX_UNEMP', 0.0), 0.0)
        self.assertPayrollEqual(cats.get('ER_US_TX_UNEMP', 0.0), 0.0)
        self.assertPayrollEqual(cats.get('ER_US_TX_OA', 0.0), 0.0)
        self.assertPayrollEqual(cats.get('ER_US_TX_ETIA', 0.0), 0.0)

    def test_payslip_example(self):
        salary = 2916.67

        employee = self._createEmployee()
        contract = self._createContract(employee, salary, struct_id=self.ref(
            'l10n_us_tx_hr_payroll.hr_payroll_salary_structure_us_tx_employee'))
        contract.w4_allowances = 2
        contract.w4_filing_status = 'single'

        self._log('2019 Texas tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_TX_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_TX_UNEMP'], cats['WAGE_US_TX_UNEMP'] * self.TX_UNEMP)
        self.assertPayrollEqual(cats['ER_US_TX_OA'], cats['WAGE_US_TX_UNEMP'] * self.TX_OA)
        self.assertPayrollEqual(cats['ER_US_TX_ETIA'], cats['WAGE_US_TX_UNEMP'] * self.TX_ETIA)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_tx_unemp_wages = self.TX_UNEMP_MAX_WAGE - salary if (self.TX_UNEMP_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2019 Texas tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_TX_UNEMP'], remaining_tx_unemp_wages)
        self.assertPayrollEqual(cats['ER_US_TX_UNEMP'], remaining_tx_unemp_wages * self.TX_UNEMP)

