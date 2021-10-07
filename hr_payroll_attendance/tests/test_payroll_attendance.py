# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo.addons.hr_payroll_hibou.tests import common
from odoo.exceptions import ValidationError


class TestAttendancePayslip(common.TestPayslip):

    def setUp(self):
        super().setUp()
        self.work_type = self.env.ref('hr_attendance_work_entry.work_input_attendance')
        self.overtime_rules = self.work_type.overtime_type_id
        self.overtime_rules.hours_per_day = 0.0
        self.overtime_rules.multiplier = 1.5
        self.test_hourly_wage = 21.5
        self.employee = self._createEmployee()
        self.contract = self._createContract(self.employee,
                                             wage=self.test_hourly_wage,
                                             hourly_wage=self.test_hourly_wage,
                                             wage_type='hourly',
                                             paid_hourly_attendance=True)

        self.work_entry_type_leave = self.env['hr.work.entry.type'].create({
            'name': 'Test PTO',
            'code': 'TESTPTO',
            'is_leave': True,
        })

    def _setup_attendance(self, employee):
        # Total 127.37 hours in 2 weeks.
        # Six 9-hour days in one week (plus a little). 58.97 hours in that week.
        attendances = self.env['hr.attendance']
        attendances += self.env['hr.attendance'].create({
            'employee_id': employee.id,
            'check_in': '2020-01-06 10:00:00',  # Monday
            'check_out': '2020-01-06 19:00:00',
        })
        attendances += self.env['hr.attendance'].create({
            'employee_id': employee.id,
            'check_in': '2020-01-07 10:00:00',
            'check_out': '2020-01-07 19:00:00',
        })
        attendances += self.env['hr.attendance'].create({
            'employee_id': employee.id,
            'check_in': '2020-01-08 10:00:00',
            'check_out': '2020-01-08 19:00:00',
        })
        attendances += self.env['hr.attendance'].create({
            'employee_id': employee.id,
            'check_in': '2020-01-09 10:00:00',
            'check_out': '2020-01-09 19:00:00',
        })
        attendances += self.env['hr.attendance'].create({
            'employee_id': employee.id,
            'check_in': '2020-01-10 10:00:00',
            'check_out': '2020-01-10 19:00:00',
        })
        attendances += self.env['hr.attendance'].create({
            'employee_id': employee.id,
            'check_in': '2020-01-11 06:00:00',
            'check_out': '2020-01-11 19:58:12',
        })

        # Five 10-hour days, Two 9-hour days (plus a little) in one week. 68.4 hours in that week
        attendances += self.env['hr.attendance'].create({
            'employee_id': employee.id,
            'check_in': '2020-01-13 08:00:00',  # Monday
            'check_out': '2020-01-13 18:00:00',
        })
        attendances += self.env['hr.attendance'].create({
            'employee_id': employee.id,
            'check_in': '2020-01-14 08:00:00',
            'check_out': '2020-01-14 18:00:00',
        })
        attendances += self.env['hr.attendance'].create({
            'employee_id': employee.id,
            'check_in': '2020-01-15 08:00:00',
            'check_out': '2020-01-15 18:00:00',
        })
        attendances += self.env['hr.attendance'].create({
            'employee_id': employee.id,
            'check_in': '2020-01-16 08:00:00',
            'check_out': '2020-01-16 18:00:00',
        })
        attendances += self.env['hr.attendance'].create({
            'employee_id': employee.id,
            'check_in': '2020-01-17 08:00:00',
            'check_out': '2020-01-17 18:00:00',
        })
        attendances += self.env['hr.attendance'].create({
            'employee_id': employee.id,
            'check_in': '2020-01-18 09:00:00',
            'check_out': '2020-01-18 18:00:00',
        })
        last = self.env['hr.attendance'].create({
            'employee_id': employee.id,
            'check_in': '2020-01-19 09:00:00',
            'check_out': '2020-01-19 18:24:00',
        })
        attendances += last
        return last

    def test_attendance_hourly(self):
        attn_last = self._setup_attendance(self.employee)
        self.payslip = self._createPayslip(self.employee, '2020-01-06', '2020-01-19')
        self.assertTrue(self.payslip.contract_id, 'No auto-discovered contract!')
        self.payslip.compute_sheet()
        # 58.97 => 40hr regular, 18.97hr OT
        # 68.4  => 40hr regular, 28.4hr  OT
        # (80 * 21.50) + (47.37 * 21.50 * 1.5) = 3247.6825
        cats = self._getCategories(self.payslip)
        self.assertAlmostEqual(cats['BASIC'], 3247.68, 2)

        # ensure unlink behavior.
        self.payslip.attendance_ids = self.env['hr.attendance'].browse()
        self.payslip.state = 'draft'
        self.payslip.flush()
        self.payslip.action_refresh_from_work_entries()
        self.payslip.compute_sheet()
        cats = self._getCategories(self.payslip)
        self.assertAlmostEqual(cats['BASIC'], 3247.68, 2)

        self.payslip.write({'attendance_ids': [(5, 0, 0)]})
        self.payslip.state = 'draft'
        self.payslip.flush()
        self.payslip.action_refresh_from_work_entries()
        self.payslip.compute_sheet()
        cats = self._getCategories(self.payslip)
        self.assertAlmostEqual(cats['BASIC'], 3247.68, 2)

        self.process_payslip()
        self.assertTrue(self.payslip.state not in ('draft', 'verify'))
        self.assertEqual(self.payslip, attn_last.payslip_id)
        # can empty, by design you have to be able to do so
        attn_last.payslip_id = False
        with self.assertRaises(ValidationError):
            # cannot re-assign as it is a finished payslip
            attn_last.payslip_id = self.payslip

    def test_with_leave(self):
        date_from = '2020-01-10'
        date_to = '2020-01-11'
        self.env['resource.calendar.leaves'].create({
            'name': 'Doctor Appointment',
            'date_from': date_from,
            'date_to': date_to,
            'resource_id': self.employee.resource_id.id,
            'calendar_id': self.employee.resource_calendar_id.id,
            'work_entry_type_id': self.work_entry_type_leave.id,
            'time_type': 'leave',
        })

        self._setup_attendance(self.employee)
        self.payslip = self._createPayslip(self.employee, '2020-01-06', '2020-01-19')
        self.assertTrue(self.payslip.worked_days_line_ids)

        leave_line = self.payslip.worked_days_line_ids.filtered(lambda l: l.code == 'TESTPTO')
        self.assertTrue(leave_line)
        self.assertEqual(leave_line.number_of_days, 1.0)
        self.assertEqual(leave_line.number_of_hours, 8.0)
        self.assertEqual(leave_line.amount, 8.0 * self.test_hourly_wage)
