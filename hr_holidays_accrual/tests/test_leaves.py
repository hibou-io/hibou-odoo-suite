from odoo.addons.hr_holidays.tests.common import TestHrHolidaysBase


class TestLeaves(TestHrHolidaysBase):

    def setUp(self):
        super(TestLeaves, self).setUp()

        self.categ = self.env['hr.employee.category'].create({'name': 'Test Category'})
        department = self.env['hr.department'].create({'name': 'Test Department'})
        self.employee = self.env['hr.employee'].create({'name': 'Mark', 'department_id': department.id})
        self.leave_type = self.env['hr.leave.type'].create({
            'name': 'Test Status',
            'color_name': 'red',
        })
        self.test_leave = self.env['hr.leave'].create({
            'holiday_status_id': self.leave_type.id,
            'number_of_days_temp': 5,
            'holiday_type': 'category',
            'category_id': self.categ.id,
            'type': 'add',
            'state': 'draft',
            'grant_by_tag': True,
        })

    def test_tag_assignment(self):
        self.test_leave.action_confirm()
        self.test_leave.action_approve()
        self.assertEqual(self.employee.leaves_count, 0.0)
        self.employee.write({'category_ids': [(6, False, [self.categ.id])]})
        self.assertEqual(self.employee.leaves_count, 5.0)
        leave = self.env['hr.leave'].search([('employee_id', '=', self.employee.id)])
        self.assertEqual(leave.holiday_status_id.id, self.leave_type.id)

    def test_double_validation(self):
        self.test_leave.write({'double_validation': True})
        self.test_leave.action_confirm()
        self.test_leave.action_approve()
        self.test_leave.action_validate()
        self.employee.write({'category_ids': [(6, False, [self.categ.id])]})
        leave = self.env['hr.leave'].search([('employee_id', '=', self.employee.id)])
        self.assertEqual(leave.state, 'validate1')
        self.assertEqual(leave.first_approver_id.id, self.env.uid)
