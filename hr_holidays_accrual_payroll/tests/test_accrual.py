from odoo.addons.hr_holidays.tests.common import TestHrHolidaysBase


class TestLeaves(TestHrHolidaysBase):

    def setUp(self):
        super(TestLeaves, self).setUp()

        self.categ = self.env['hr.employee.category'].create({'name': 'Test Category'})
        department = self.env['hr.department'].create({'name': 'Test Department'})
        self.employee = self.env['hr.employee'].create({'name': 'Mark', 'department_id': department.id})
        self.leave_type = self.env['hr.holidays.status'].create({
            'name': 'Test Status',
            'color_name': 'red',
        })
        self.test_leave = self.env['hr.holidays'].create({
            'holiday_status_id': self.leave_type.id,
            'number_of_days_temp': 0,
            'holiday_type': 'category',
            'category_id': self.categ.id,
            'type': 'add',
            'state': 'draft',
            'grant_by_tag': True,
        })

    def test_payslip_accrual(self):
        self.test_leave.write({
            'accrue_by_pay_period': True,
            'allocation_per_period': 1
        })
        self.test_leave.action_confirm()
        self.test_leave.action_approve()

        self.employee.write({'category_ids': [(6, False, [self.categ.id])]})
        self.assertEqual(self.employee.leaves_count, 0.0)

        payslip = self.env['hr.payslip'].create({
            'employee_id': self.employee.id,
            'date_from': '2018-01-01',
            'date_to': '2018-01-31'
        })
        payslip.action_payslip_done()
        self.assertEqual(self.employee.leaves_count, 1.0)
