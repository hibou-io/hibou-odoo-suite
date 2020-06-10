# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields
from odoo.addons.l10n_us_hr_payroll.tests import common
from datetime import timedelta


class TestUsPayslip(common.TestUsPayslip):
    EE_LIMIT = 19500.0
    EE_LIMIT_CATCHUP = 6500.0
    ER_LIMIT = 37500.0

    def setUp(self):
        super().setUp()
        self.schedule_pay_salary = 'bi-weekly'
        self.payslip_date_start = fields.Date.from_string('2020-01-01')
        self.payslip_date_end = self.payslip_date_start + timedelta(days=14)
        self.er_match_parameter = self.env.ref('l10n_us_hr_payroll_401k.rule_parameter_er_401k_match_percent_2020')
        self.er_match_parameter.parameter_value = '4.0'  # 4% match up to salary

    def test_01_payslip_traditional(self):
        wage = 2000.0
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        ira_rate=5.0,
                                        schedule_pay=self.schedule_pay_salary)
        payslip = self._createPayslip(employee, self.payslip_date_start, self.payslip_date_end)
        payslip.compute_sheet()
        ira_line = payslip.line_ids.filtered(lambda l: l.code == 'EE_IRA')
        self.assertTrue(ira_line)
        self.assertPayrollEqual(ira_line.amount, -100.0)

        er_ira_line = payslip.line_ids.filtered(lambda l: l.code == 'ER_IRA_MATCH')
        self.assertTrue(er_ira_line)
        self.assertPayrollEqual(er_ira_line.amount, 80.0)  # 4% of wage up to their contribution

        contract.ira_rate = 0.0
        contract.ira_amount = 25.0
        payslip.compute_sheet()
        ira_line = payslip.line_ids.filtered(lambda l: l.code == 'EE_IRA')
        self.assertTrue(ira_line)
        self.assertPayrollEqual(ira_line.amount, -25.0)

        er_ira_line = payslip.line_ids.filtered(lambda l: l.code == 'ER_IRA_MATCH')
        self.assertTrue(er_ira_line)
        self.assertPayrollEqual(er_ira_line.amount, 25.0)  # 4% of wage up to their contribution

    def test_02_payslip_roth(self):
        wage = 2000.0
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        ira_roth_rate=5.0,
                                        schedule_pay=self.schedule_pay_salary)
        payslip = self._createPayslip(employee, self.payslip_date_start, self.payslip_date_end)
        payslip.compute_sheet()
        ira_line = payslip.line_ids.filtered(lambda l: l.code == 'EE_IRA_ROTH')
        self.assertTrue(ira_line)
        self.assertPayrollEqual(ira_line.amount, -100.0)

        er_ira_line = payslip.line_ids.filtered(lambda l: l.code == 'ER_IRA_MATCH')
        self.assertTrue(er_ira_line)
        self.assertPayrollEqual(er_ira_line.amount, 80.0)  # 4% of wage up to their contribution

        contract.ira_roth_rate = 0.0
        contract.ira_roth_amount = 25.0
        payslip.compute_sheet()
        ira_line = payslip.line_ids.filtered(lambda l: l.code == 'EE_IRA_ROTH')
        self.assertTrue(ira_line)
        self.assertPayrollEqual(ira_line.amount, -25.0)

        er_ira_line = payslip.line_ids.filtered(lambda l: l.code == 'ER_IRA_MATCH')
        self.assertTrue(er_ira_line)
        self.assertPayrollEqual(er_ira_line.amount, 25.0)  # 4% of wage up to their contribution

    def test_10_payslip_limits(self):
        self.er_match_parameter.parameter_value = '20.0'  # 20% match up to salary
        wage = 80000.0
        rate = 20.0
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        ira_rate=rate,
                                        schedule_pay=self.schedule_pay_salary)

        # Payslip 1 - 16k
        payslip = self._createPayslip(employee, self.payslip_date_start, self.payslip_date_end)
        payslip.compute_sheet()
        ira_line = payslip.line_ids.filtered(lambda l: l.code == 'EE_IRA')
        self.assertTrue(ira_line)
        self.assertPayrollEqual(ira_line.amount, -(wage * rate / 100.0))
        er_ira_line = payslip.line_ids.filtered(lambda l: l.code == 'ER_IRA_MATCH')
        self.assertTrue(er_ira_line)
        self.assertPayrollEqual(er_ira_line.amount, -ira_line.amount)
        common.process_payslip(payslip)

        # Payslip 2 - 3.5k
        payslip = self._createPayslip(employee, self.payslip_date_start + timedelta(days=14),
                                      self.payslip_date_end + timedelta(days=14))
        payslip.compute_sheet()
        ira_line = payslip.line_ids.filtered(lambda l: l.code == 'EE_IRA')
        self.assertTrue(ira_line)
        self.assertPayrollEqual(ira_line.amount, -(self.EE_LIMIT-(wage * rate / 100.0)))
        er_ira_line = payslip.line_ids.filtered(lambda l: l.code == 'ER_IRA_MATCH')
        self.assertTrue(er_ira_line)
        self.assertPayrollEqual(er_ira_line.amount, -ira_line.amount)
        common.process_payslip(payslip)

        # Payslip 3 - 0 (over limit)
        payslip = self._createPayslip(employee, self.payslip_date_start + timedelta(days=28),
                                      self.payslip_date_end + timedelta(days=28))
        payslip.compute_sheet()
        ira_line = payslip.line_ids.filtered(lambda l: l.code == 'EE_IRA')
        self.assertFalse(ira_line)
        er_ira_line = payslip.line_ids.filtered(lambda l: l.code == 'ER_IRA_MATCH')
        self.assertFalse(er_ira_line)

        # Payslip 3 - Catch-up
        employee.birthday = '1960-01-01'
        payslip.compute_sheet()
        ira_line = payslip.line_ids.filtered(lambda l: l.code == 'EE_IRA')
        self.assertTrue(ira_line)
        self.assertPayrollEqual(ira_line.amount, -self.EE_LIMIT_CATCHUP)
        er_ira_line = payslip.line_ids.filtered(lambda l: l.code == 'ER_IRA_MATCH')
        self.assertTrue(er_ira_line)
        self.assertPayrollEqual(er_ira_line.amount, -ira_line.amount)
        common.process_payslip(payslip)

        # Note that the company limit is higher than what is possible by 'match'
        # because even with 100% (or more) you would never be able to out-pace
        # the employee's own contributions.
