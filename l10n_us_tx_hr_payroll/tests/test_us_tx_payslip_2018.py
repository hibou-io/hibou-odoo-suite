from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip
from odoo.addons.l10n_us_hr_payroll.models.l10n_us_hr_payroll import USHrContract


class TestUsTXPayslip(TestUsPayslip):
    ###
    #   2018 Taxes and Rates
    ###
    TX_UNEMP_MAX_WAGE = 9000.0

    def test_2018_taxes(self):
        salary = 5000.0

        employee = self._createEmployee()
        employee.company_id.tx_unemp_rate_2018 = 2.7
        employee.company_id.tx_oa_rate_2018 = 0.0
        employee.company_id.tx_etia_rate_2018 = 0.1

        contract = self._createContract(employee, salary, struct_id=self.ref('l10n_us_tx_hr_payroll.hr_payroll_salary_structure_us_tx_employee'))

        # tax rates
        tx_unemp = contract.tx_unemp_rate(2018) / -100.0
        tx_oa = contract.tx_oa_rate(2018) / -100.00
        tx_etia = contract.tx_etia_rate(2018) / -100.00

        self._log('2018 Texas tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['TX_UNEMP_WAGES'], salary)
        self.assertPayrollEqual(cats['TX_UNEMP'], cats['TX_UNEMP_WAGES'] * tx_unemp)
        self.assertPayrollEqual(cats['TX_OA'], cats['TX_UNEMP_WAGES'] * tx_oa)
        self.assertPayrollEqual(cats['TX_ETIA'], cats['TX_UNEMP_WAGES'] * tx_etia)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_tx_unemp_wages = self.TX_UNEMP_MAX_WAGE - salary if (self.TX_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2018 Texas tax second payslip:')
        payslip = self._createPayslip(employee, '2018-02-01', '2018-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['TX_UNEMP_WAGES'], remaining_tx_unemp_wages)
        self.assertPayrollEqual(cats['TX_UNEMP'], remaining_tx_unemp_wages * tx_unemp)

    def test_2018_taxes_with_external(self):
        salary = 5000.0
        external_wages = 6000.0

        employee = self._createEmployee()
        employee.company_id.tx_unemp_rate_2018 = 2.7
        employee.company_id.tx_oa_rate_2018 = 0.0
        employee.company_id.tx_etia_rate_2018 = 0.1

        contract = self._createContract(employee, salary, external_wages=external_wages,
                                        struct_id=self.ref('l10n_us_tx_hr_payroll.hr_payroll_salary_structure_us_tx_employee'))

        # tax rates
        tx_unemp = contract.tx_unemp_rate(2018) / -100.0
        tx_oa = contract.tx_oa_rate(2018) / -100.00
        tx_etia = contract.tx_etia_rate(2018) / -100.00

        self._log('2018 Texas_external tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['TX_UNEMP_WAGES'], self.TX_UNEMP_MAX_WAGE - external_wages)
        self.assertPayrollEqual(cats['TX_UNEMP'], cats['TX_UNEMP_WAGES'] * tx_unemp)
        self.assertPayrollEqual(cats['TX_OA'], cats['TX_UNEMP_WAGES'] * tx_oa)
        self.assertPayrollEqual(cats['TX_ETIA'], cats['TX_UNEMP_WAGES'] * tx_etia)

    def test_2018_taxes_with_state_exempt(self):
        salary = 5000.0
        external_wages = 6000.0

        employee = self._createEmployee()
        employee.company_id.tx_unemp_rate_2018 = 2.7
        employee.company_id.tx_oa_rate_2018 = 0.0
        employee.company_id.tx_etia_rate_2018 = 0.1

        contract = self._createContract(employee, salary, external_wages=external_wages, struct_id=self.ref(
            'l10n_us_tx_hr_payroll.hr_payroll_salary_structure_us_tx_employee'), futa_type=USHrContract.FUTA_TYPE_BASIC)

        # tax rates
        tx_unemp = contract.tx_unemp_rate(2018) / -100.0
        tx_oa = contract.tx_oa_rate(2018) / -100.00
        tx_etia = contract.tx_etia_rate(2018) / -100.00

        self.assertPayrollEqual(tx_unemp, 0.0)

        self._log('2018 Texas_external tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['TX_UNEMP_WAGES'], self.TX_UNEMP_MAX_WAGE - external_wages)
        self.assertPayrollEqual(cats['TX_UNEMP'], cats['TX_UNEMP_WAGES'] * tx_unemp)
        self.assertPayrollEqual(cats['TX_OA'], cats['TX_UNEMP_WAGES'] * tx_oa)
        self.assertPayrollEqual(cats['TX_ETIA'], cats['TX_UNEMP_WAGES'] * tx_etia)

    def test_payslip_example(self):
        salary = 2916.67

        employee = self._createEmployee()
        employee.company_id.tx_unemp_rate_2018 = 2.7
        employee.company_id.tx_oa_rate_2018 = 0.0
        employee.company_id.tx_etia_rate_2018 = 0.1

        contract = self._createContract(employee, salary, struct_id=self.ref(
            'l10n_us_tx_hr_payroll.hr_payroll_salary_structure_us_tx_employee'))
        contract.w4_allowances = 2
        contract.w4_filing_status = 'single'

        # tax rates
        tx_unemp = contract.tx_unemp_rate(2018) / -100.0
        tx_oa = contract.tx_oa_rate(2018) / -100.00
        tx_etia = contract.tx_etia_rate(2018) / -100.00

        self._log('2018 Texas tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['TX_UNEMP_WAGES'], salary)
        self.assertPayrollEqual(cats['TX_UNEMP'], cats['TX_UNEMP_WAGES'] * tx_unemp)
        self.assertPayrollEqual(cats['TX_OA'], cats['TX_UNEMP_WAGES'] * tx_oa)
        self.assertPayrollEqual(cats['TX_ETIA'], cats['TX_UNEMP_WAGES'] * tx_etia)

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_tx_unemp_wages = self.TX_UNEMP_MAX_WAGE - salary if (self.TX_UNEMP_MAX_WAGE - 2 * salary < salary) \
            else salary

        self._log('2018 Texas tax second payslip:')
        payslip = self._createPayslip(employee, '2018-02-01', '2018-02-28')

        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['TX_UNEMP_WAGES'], remaining_tx_unemp_wages)
        self.assertPayrollEqual(cats['TX_UNEMP'], remaining_tx_unemp_wages * tx_unemp)

