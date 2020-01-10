# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date
from .common import TestUsPayslip, process_payslip


class TestUsWAPayslip(TestUsPayslip):
    ###
    #    Taxes and Rates
    ###
    WA_UNEMP_MAX_WAGE = 52700.00
    WA_UNEMP_RATE = 1.0
    WA_FML_MAX_WAGE = 137700.00
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
                'date_from': date(2020, 1, 1),
                'parameter_value': str(self.test_ee_lni * 100),
            })],
        })
        self.parameter_lni_er = self.env['hr.rule.parameter'].create({
            'name': 'Test LNI ER',
            'code': 'test_lni_er',
            'parameter_version_ids': [(0, 0, {
                'date_from': date(2020, 1, 1),
                'parameter_value': str(self.test_er_lni * 100),
            })],
        })

    def test_2020_taxes(self):
        self._test_er_suta('WA', self.WA_UNEMP_RATE, date(2020, 1, 1), wage_base=self.WA_UNEMP_MAX_WAGE)

        salary = (self.WA_FML_MAX_WAGE / 2.0) + 1000.0

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('WA'),
                                        workers_comp_ee_code=self.parameter_lni_ee.code,
                                        workers_comp_er_code=self.parameter_lni_er.code,
                                        )
        self._log(str(contract.resource_calendar_id) + ' ' + contract.resource_calendar_id.name)


        # Non SUTA
        self._log('2020 Washington tax first payslip:')
        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')
        hours_in_period = payslip.worked_days_line_ids.filtered(lambda l: l.code == 'WORK100').number_of_hours
        self.assertEqual(hours_in_period, 184)  # only asserted to test algorithm
        payslip.compute_sheet()

        rules = self._getRules(payslip)

        self.assertPayrollEqual(rules['EE_US_WA_LNI'], -(self.test_ee_lni * hours_in_period))
        self.assertPayrollEqual(rules['ER_US_WA_LNI'], -(self.test_er_lni * hours_in_period))
        # Both of these are known to be within 1 penny
        self.assertPayrollAlmostEqual(rules['EE_US_WA_FML'], -(salary * (self.WA_FML_RATE / 100.0) * (self.WA_FML_RATE_EE / 100.0)))
        self.assertPayrollAlmostEqual(rules['ER_US_WA_FML'], -(salary * (self.WA_FML_RATE / 100.0) * (self.WA_FML_RATE_ER / 100.0)))
        process_payslip(payslip)

        # Second payslip
        remaining_wage = self.WA_FML_MAX_WAGE - salary
        payslip = self._createPayslip(employee, '2020-03-01', '2020-03-31')
        payslip.compute_sheet()
        rules = self._getRules(payslip)
        self.assertPayrollAlmostEqual(rules['EE_US_WA_FML'], -(remaining_wage * (self.WA_FML_RATE / 100.0) * (self.WA_FML_RATE_EE / 100.0)))
        self.assertPayrollAlmostEqual(rules['ER_US_WA_FML'], -(remaining_wage * (self.WA_FML_RATE / 100.0) * (self.WA_FML_RATE_ER / 100.0)))
        process_payslip(payslip)

        # Third payslip
        payslip = self._createPayslip(employee, '2020-04-01', '2020-04-30')
        payslip.compute_sheet()
        rules = self._getRules(payslip)
        self.assertPayrollAlmostEqual(rules['EE_US_WA_FML'], 0.0)
        self.assertPayrollAlmostEqual(rules['ER_US_WA_FML'], 0.0)
