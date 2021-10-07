from odoo.tests import common


class TestTimesheetWorkType(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.employee = self.env.ref('hr.employee_hne')
        self.project = self.env.ref('project.project_project_2')
        self.default_work_type = self.env.ref('hr_timesheet_work_entry.work_input_timesheet')

    def test_01_work_type(self):
        timesheet = self.env['account.analytic.line'].create({
            'name': '/',
            'employee_id': self.employee.id,
            'unit_amount': 1.0,
            'project_id': self.project.id,
        })
        self.assertTrue(timesheet.work_type_id)
        self.assertEqual(timesheet.work_type_id, self.default_work_type)
