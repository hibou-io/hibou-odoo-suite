# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date
from .common import TestUsPayslip, process_payslip


class TestUsWAPayslip(TestUsPayslip):
    ###
    #    Taxes and Rates
    ###
    WA_UNEMP_MAX_WAGE = 49800.0
    WA_UNEMP_RATE = 1.18
    WA_FML_RATE = 0.4
    WA_FML_RATE_EE = 66.33
    WA_FML_RATE_ER = 33.67

    def setUp(self):
        super(TestUsWAPayslip, self).setUp()
        # self.lni = self.env['hr.contract.lni.wa'].create({
        #     'name': '5302 Computer Consulting',
        #     'rate': 0.1261,
        #     'rate_emp_withhold': 0.05575,
        # })
        self.test_ee_lni = 0.05575  # per 100 hours
        self.test_er_lni = 0.1261  # per 100 hours
        self.parameter_lni_ee = self.env['hr.rule.parameter'].create({
            'name': 'Test LNI EE',
            'code': 'test_lni_ee',
            'parameter_version_ids': [(0, 0, {
                'date_from': date(2019, 1, 1),
                'parameter_value': str(self.test_ee_lni * 100),
            })],
        })
        self.parameter_lni_er = self.env['hr.rule.parameter'].create({
            'name': 'Test LNI ER',
            'code': 'test_lni_er',
            'parameter_version_ids': [(0, 0, {
                'date_from': date(2019, 1, 1),
                'parameter_value': str(self.test_er_lni * 100),
            })],
        })

    def test_2019_taxes(self):
        salary = 25000.0

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('WA'),
                                        workers_comp_ee_code=self.parameter_lni_ee.code,
                                        workers_comp_er_code=self.parameter_lni_er.code,
                                        )
        self._log(str(contract.resource_calendar_id) + ' ' + contract.resource_calendar_id.name)


        # tax rates
        wa_unemp = self.WA_UNEMP_RATE / -100.0

        self._log('2019 Washington tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        hours_in_period = payslip.worked_days_line_ids.filtered(lambda l: l.code == 'WORK100').number_of_hours
        self.assertEqual(hours_in_period, 184)  # only asserted to test algorithm
        payslip.compute_sheet()


        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], salary * wa_unemp)
        self.assertPayrollEqual(rules['EE_US_WA_LNI'], -(self.test_ee_lni * hours_in_period))
        self.assertPayrollEqual(rules['ER_US_WA_LNI'], -(self.test_er_lni * hours_in_period))
        # Both of these are known to be within 1 penny
        self.assertPayrollAlmostEqual(rules['EE_US_WA_FML'], -(salary * (self.WA_FML_RATE / 100.0) * (self.WA_FML_RATE_EE / 100.0)))
        self.assertPayrollAlmostEqual(rules['ER_US_WA_FML'], -(salary * (self.WA_FML_RATE / 100.0) * (self.WA_FML_RATE_ER / 100.0)))

        # FML

        process_payslip(payslip)

        # Make a new payslip, this one will have maximums

        remaining_wa_unemp_wages = self.WA_UNEMP_MAX_WAGE - salary if (self.WA_UNEMP_MAX_WAGE - 2*salary < salary) \
            else salary

        self._log('2019 Washington tax second payslip:')
        payslip = self._createPayslip(employee, '2019-02-01', '2019-02-28')
        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['ER_US_SUTA'], remaining_wa_unemp_wages * wa_unemp)
