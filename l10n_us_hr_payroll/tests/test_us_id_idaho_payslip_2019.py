# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip


class TestUsIDPayslip(TestUsPayslip):

    # TAXES AND RATES
    ID_UNEMP_MAX_WAGE = 40000.00
    ID_UNEMP = -(1.00 / 100.0)

    def test_taxes_single_biweekly(self):
        salary = 1212.00
        schedule_pay = 'bi-weekly'
        filing_status = 'single'
        allowances = 4
        # SEE https://tax.idaho.gov/i-1026.cfm?seg=compute for example calculations
        wh_to_check = -10.00
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('ID'),
                                        id_w4_sit_filing_status=filing_status,
                                        id_w4_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)

        self._log('2019 Idaho tax first payslip single:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.ID_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh_to_check)

        process_payslip(payslip)

        remaining_id_unemp_wages = self.ID_UNEMP_MAX_WAGE - salary if (self.ID_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2019 Idaho tax second payslip single:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_id_unemp_wages * self.ID_UNEMP)

    def test_taxes_married_monthly(self):
        salary = 5000.00
        schedule_pay = 'monthly'
        filing_status = 'married'
        allowances = 2

        # ICTCAT says monthly allowances are 246.67
        # we have 2 so 246.67 * 2 = 493.34
        # 5000.00 - 493.34 = 4506.66
        # Wh is 89$ plus 6.925% over 3959,00
        # 126.92545499999999 - > 127.0
        wh_to_check = -127.0
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('ID'),
                                        id_w4_sit_filing_status=filing_status,
                                        id_w4_sit_allowances=allowances,
                                        schedule_pay=schedule_pay)

        self._log('2019 Idaho tax first payslip monthly:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * self.ID_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh_to_check)

        process_payslip(payslip)

        remaining_id_unemp_wages = self.ID_UNEMP_MAX_WAGE - salary if (self.ID_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2019 Idaho tax second payslip monthly:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_id_unemp_wages * self.ID_UNEMP)
