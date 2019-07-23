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
        self.allocation = self.env['hr.leave.allocation'].create({
            'employee_id': self.employee.id,
            'holiday_status_id': self.leave_type.id,
            'number_of_days': 0.0,
            'state': 'validate',
            'accrual': True,
            'holiday_type': 'employee',
            'number_per_interval': 0.75,
            'unit_per_interval': 'days',
            'interval_unit': 'payslip',
            'accrual_limit': 1,
        })

    def test_payslip_accrual(self):
        payslip = self.env['hr.payslip'].create({
            'employee_id': self.employee.id,
            'date_from': '2018-01-01',
            'date_to': '2018-01-31'
        })
        payslip.action_payslip_done()
        self.assertEqual(self.allocation.number_of_days, 0.75)

        # Should be capped at 1 day
        payslip = self.env['hr.payslip'].create({
            'employee_id': self.employee.id,
            'date_from': '2018-02-01',
            'date_to': '2018-02-28'
        })
        payslip.action_payslip_done()
        self.assertEqual(self.allocation.number_of_days, 1.0)
