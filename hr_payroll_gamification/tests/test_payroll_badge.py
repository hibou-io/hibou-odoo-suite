from odoo.addons.hr_payroll_hibou.tests import common
from odoo import fields
from datetime import date


class TestPayslip(common.TestPayslip):

    def setUp(self):
        super(TestPayslip, self).setUp()
        self.wage = 2000.00
        self.structure = self.env.ref('hr_payroll.structure_002')
        self.structure_type = self.structure.type_id
        self.structure_type.wage_type = 'monthly'
        self.employee = self._createEmployee()
        self.employee.user_id = self.env.user
        self.contract = self._createContract(self.employee, wage=self.wage)

    def test_badge_amounts(self):
        badge = self.env['gamification.badge'].create({
            'name': 'test',
        })
        badge.payroll_amount = 5.0

    def test_badge_payroll(self):
        additional_wage = 5.0
        additional_wage_period = 15.0
        payslip = self._createPayslip(self.employee,
                                      '2018-01-01',
                                      '2018-01-31',
                                      )
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertEqual(cats['BASIC'], self.wage)

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
        payslip = self._createPayslip(self.employee,
                                      '2018-01-01',
                                      '2018-01-31',)
        self.assertTrue(payslip.input_line_ids)
        input_line = payslip.input_line_ids.filtered(lambda l: l.name == 'Badges')
        self.assertTrue(input_line)
        self.assertEqual(input_line.amount, additional_wage)
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertEqual(cats['BASIC'], self.wage + additional_wage)

         
        # Include both Badges
        payslip = self._createPayslip(self.employee,
                                '2018-02-01',
                                '2018-02-25',)
        input_line = payslip.input_line_ids.filtered(lambda l: l.name == 'Badges')
        self.assertTrue(input_line)
        self.assertEqual(input_line.amount, additional_wage + additional_wage_period)
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertEqual(cats['BASIC'], self.wage + additional_wage + additional_wage_period)
