from odoo.addons.l10n_us_hr_payroll.tests.test_us_payslip import TestUsPayslip, process_payslip


class TestUsWAPayslip(TestUsPayslip):
    ###
    #    Taxes and Rates
    ###
    WA_UNEMP_MAX_WAGE = 47300.0
    WA_UNEMP_RATE = 1.16

    def setUp(self):
        super(TestUsWAPayslip, self).setUp()
        self.lni = self.env['hr.contract.lni.wa'].create({
            'name': '5302 Computer Consulting',
            'rate': 0.1261,
            'rate_emp_withhold': 0.05575,
        })

    def test_2018_taxes(self):
        salary = 25000.0

        employee = self._createEmployee()

        contract = self._createContract(employee, salary, struct_id=self.ref('l10n_us_wa_hr_payroll.hr_payroll_salary_structure_us_wa_employee'))
        self._log(str(contract.resource_calendar_id) + ' ' + contract.resource_calendar_id.name)
        contract.wa_lni = self.lni

        # tax rates
        wa_unemp = self.WA_UNEMP_RATE / -100.0

        self._log('2018 Washington tax first payslip:')
        payslip = self._createPayslip(employee, '2018-01-01', '2018-01-31')
        payslip.onchange_contract()
        hours_in_period = payslip.worked_days_line_ids.filtered(lambda l: l.code == 'WORK100').number_of_hours
        payslip.compute_sheet()


        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_WA_UNEMP'], salary)
        self.assertPayrollEqual(cats['ER_US_WA_UNEMP'], cats['WAGE_US_WA_UNEMP'] * wa_unemp)
        self.assertPayrollEqual(cats['EE_US_WA_LNI'], -(self.lni.rate_emp_withhold * hours_in_period))
        self.assertPayrollEqual(cats['ER_US_WA_LNI'], -(self.lni.rate * hours_in_period) - cats['EE_US_WA_LNI'])

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_wa_unemp_wages = self.WA_UNEMP_MAX_WAGE - salary if (self.WA_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2018 Washington tax second payslip:')
        payslip = self._createPayslip(employee, '2018-02-01', '2018-02-28')
        payslip.onchange_contract()
        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['WAGE_US_WA_UNEMP'], remaining_wa_unemp_wages)
        self.assertPayrollEqual(cats['ER_US_WA_UNEMP'], remaining_wa_unemp_wages * wa_unemp)
