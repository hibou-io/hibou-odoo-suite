from odoo.tests import common
from odoo import fields
from datetime import date


class TestPayroll(common.TransactionCase):

    def setUp(self):
        super(TestPayroll, self).setUp()
        self.wage = 21.50
        self.employee = self.env['hr.employee'].create({
            'birthday': '1985-03-14',
            'country_id': self.ref('base.us'),
            'department_id': self.ref('hr.dep_rd'),
            'gender': 'male',
            'name': 'Jared',
            'user_id': self.env.user.id,
        })
        self.contract = self.env['hr.contract'].create({
            'name': 'test',
            'employee_id': self.employee.id,
            'type_id': self.ref('hr_contract.hr_contract_type_emp'),
            'struct_id': self.ref('hr_payroll.structure_base'),
            'resource_calendar_id': self.ref('resource.resource_calendar_std'),
            'wage': self.wage,
            'date_start': '2018-01-01',
            'state': 'open',
            'schedule_pay': 'monthly',
        })

    def test_badge_amounts(self):
        badge = self.env['gamification.badge'].create({
            'name': 'test',
        })
        badge.payroll_amount = 5.0

    def test_badge_payroll(self):
        additional_wage = 5.0
        additional_wage_period = 15.0
        payslip = self.env['hr.payslip'].create({
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'date_from': '2018-01-01',
            'date_to': '2018-01-31',
        })
        self.assertEqual(payslip._get_input_badges(self.contract, date(2018, 1, 1), date(2018, 1, 31)), 0.0)
        payslip.compute_sheet()
        basic = payslip.details_by_salary_rule_category.filtered(lambda l: l.code == 'GROSS')
        self.assertTrue(basic)
        self.assertEqual(basic.total, self.wage)

        badge = self.env['gamification.badge'].create({
            'name': 'test',
            'payroll_type': 'fixed',
            'payroll_amount': additional_wage,
        })

        badge_user = self.env['gamification.badge.user'].create({
            'badge_id': badge.id,
            'employee_id': self.employee.id,
            'user_id': self.env.user.id,
        })

        badge_period = self.env['gamification.badge'].create({
            'name': 'test period',
            'payroll_type': 'period',
            'payroll_amount': additional_wage_period,
        })

        # Need a specific 'create_date' to test.
        badge_user_period = self.env['gamification.badge.user'].create({
            'badge_id': badge_period.id,
            'employee_id': self.employee.id,
            'user_id': self.env.user.id,
        })
        self.env.cr.execute('update gamification_badge_user set create_date = \'2018-02-10\' where id = %d;' % (badge_user_period.id, ))
        badge_user_period = self.env['gamification.badge.user'].browse(badge_user_period.id)

        self.assertEqual(self.employee.badge_ids, badge_user + badge_user_period)

        # Includes only one badge
        payslip = self.env['hr.payslip'].create({
            'employee_id': self.employee.id,
            'date_from': '2018-01-01',
            'date_to': '2018-01-31',
        })
        # This is crazy, but...
        res = payslip.onchange_employee_id(date(2018, 1, 1), date(2018, 1, 31), employee_id=self.employee.id, contract_id=self.contract.id)
        del res['value']['line_ids']
        res['value']['input_line_ids'] = [(0, 0, l) for l in res['value']['input_line_ids']]
        res['value']['worked_days_line_ids'] = [(0, 0, l) for l in res['value']['worked_days_line_ids']]
        payslip.write(res['value'])
        self.assertTrue(payslip.input_line_ids)
        payslip.compute_sheet()

        self.assertEqual(payslip._get_input_badges(self.contract, date(2018, 1, 1), date(2018, 1, 31)), additional_wage)

        basic = payslip.details_by_salary_rule_category.filtered(lambda l: l.code == 'GROSS')
        self.assertTrue(basic)
        self.assertEqual(basic.total, self.wage + additional_wage)

        # Include both Badges
        payslip = self.env['hr.payslip'].create({
            'employee_id': self.employee.id,
            'date_from': '2018-02-01',
            'date_to': '2018-02-25',  # Feb...
        })
        # This is crazy, but...
        res = payslip.onchange_employee_id(date(2018, 2, 1), date(2018, 2, 25), employee_id=self.employee.id,
                                           contract_id=self.contract.id)
        del res['value']['line_ids']
        res['value']['input_line_ids'] = [(0, 0, l) for l in res['value']['input_line_ids']]
        res['value']['worked_days_line_ids'] = [(0, 0, l) for l in res['value']['worked_days_line_ids']]
        payslip.write(res['value'])
        self.assertTrue(payslip.input_line_ids)
        payslip.compute_sheet()

        self.assertEqual(payslip._get_input_badges(self.contract, date(2018, 2, 1), date(2018, 2, 25)), additional_wage + additional_wage_period)

        basic = payslip.details_by_salary_rule_category.filtered(lambda l: l.code == 'GROSS')
        self.assertTrue(basic)
        self.assertEqual(basic.total, self.wage + additional_wage + additional_wage_period)
