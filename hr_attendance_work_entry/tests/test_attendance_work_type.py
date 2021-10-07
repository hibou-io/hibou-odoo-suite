from time import sleep
from odoo.tests import common


class TestAttendanceWorkType(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.employee = self.env.ref('hr.employee_hne')
        self.default_work_type = self.env.ref('hr_attendance_work_entry.work_input_attendance')

    def test_01_work_type(self):
        attendance = self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': '2020-01-06 10:00:00',  # Monday
            'check_out': '2020-01-06 19:00:00',
        })
        self.assertTrue(attendance.work_type_id)
        self.assertEqual(attendance.work_type_id, self.default_work_type)

    def test_11_employee_clock_in(self):
        self.assertEqual(self.employee.attendance_state, 'checked_out')
        attendance = self.employee._attendance_action_change()
        self.assertEqual(attendance.work_type_id, self.default_work_type)
        self.assertEqual(self.employee.attendance_state, 'checked_in')

        # check out
        self.employee._attendance_action_change()
        self.assertEqual(self.employee.attendance_state, 'checked_out')

    def test_12_employee_clock_in_break(self):
        # check in with non-standard work type
        break_type = self.env['hr.work.entry.type'].create({
            'name': 'Test Break',
            'code': 'TESTBREAK',
            'allow_attendance': True,
            'attendance_state': 'break',
        })
        self.employee = self.employee.with_context(work_type_id=break_type.id)
        attendance = self.employee._attendance_action_change()
        self.assertEqual(attendance.work_type_id, break_type)
        self.assertEqual(self.employee.attendance_state, 'break')

        # tests likely won't pass as the timestamps will be the same
        sleep(1)

        # check back in immediately with default
        self.employee = self.employee.with_context(work_type_id=self.default_work_type.id)
        attendance = self.employee._attendance_action_change()
        self.assertEqual(attendance.work_type_id, self.default_work_type)
        self.assertEqual(attendance.work_type_id.attendance_state, 'checked_in')
        self.assertEqual(self.employee.last_attendance_id, attendance)
        self.assertEqual(self.employee.attendance_state, 'checked_in')
