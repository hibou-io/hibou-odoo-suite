from odoo.tests import common
from odoo import fields


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
        payslip = self.env['hr.payslip'].create({
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'date_from': '2018-01-01',
            'date_to': '2018-01-31',
        })
        self.assertEqual(payslip._get_input_badges(self.contract, '2018-01-01', '2018-01-31'), 0.0)
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

        self.assertEqual(self.employee.badge_ids, badge_user)

        payslip = self.env['hr.payslip'].create({
            'employee_id': self.employee.id,
            'contract_id': self.contract.id,
            'date_from': '2018-01-01',
            'date_to': '2018-01-31',
        })
        payslip.onchange_employee_id('2018-01-01', '2018-01-31', employee_id=self.employee.id, contract_id=self.contract.id)
        payslip.compute_sheet()
        self.assertEqual(payslip._get_input_badges(self.contract, '2018-01-01', '2018-01-31'), 5.0)
        self.assertTrue(payslip.contract_id)
        basic = payslip.details_by_salary_rule_category.filtered(lambda l: l.code == 'GROSS')
        self.assertTrue(basic)
        self.assertEqual(basic.total, self.wage + additional_wage)






    # def test_payroll_rate_multicompany(self):
    #     test_rate_other = self.env['hr.payroll.rate'].create({
    #         'name': 'Test Rate',
    #         'code': 'TEST',
    #         'rate': 1.65,
    #         'date_from': '2018-01-01',
    #         'company_id': self.company_other.id,
    #     })
    #     rate = self.payslip.get_rate('TEST')
    #     self.assertFalse(rate)
    #     test_rate = self.env['hr.payroll.rate'].create({
    #         'name': 'Test Rate',
    #         'code': 'TEST',
    #         'rate': 1.65,
    #         'date_from': '2018-01-01',
    #     })
    #
    #     rate = self.payslip.get_rate('TEST')
    #     self.assertEqual(rate, test_rate)
    #
    #     test_rate_more_specific = self.env['hr.payroll.rate'].create({
    #         'name': 'Test Rate Specific',
    #         'code': 'TEST',
    #         'rate': 1.65,
    #         'date_from': '2018-01-01',
    #         'company_id': self.payslip.company_id.id,
    #     })
    #     rate = self.payslip.get_rate('TEST')
    #     self.assertEqual(rate, test_rate_more_specific)
    #
    # def test_payroll_rate_newer(self):
    #     test_rate_old = self.env['hr.payroll.rate'].create({
    #         'name': 'Test Rate',
    #         'code': 'TEST',
    #         'rate': 1.65,
    #         'date_from': '2018-01-01',
    #     })
    #     test_rate = self.env['hr.payroll.rate'].create({
    #         'name': 'Test Rate',
    #         'code': 'TEST',
    #         'rate': 2.65,
    #         'date_from': '2019-01-01',
    #     })
    #
    #     rate = self.payslip.get_rate('TEST')
    #     self.assertEqual(rate, test_rate)
    #
    # def test_payroll_rate_precision(self):
    #     test_rate = self.env['hr.payroll.rate'].create({
    #         'name': 'Test Rate',
    #         'code': 'TEST',
    #         'rate': 2.65001,
    #         'date_from': '2019-01-01',
    #     })
    #     self.assertEqual(round(test_rate.rate * 100000), 265001.0)
