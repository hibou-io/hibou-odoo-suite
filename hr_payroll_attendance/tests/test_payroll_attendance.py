from collections import defaultdict
from odoo.tests import common


class TestUsPayslip(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.test_hourly_wage = 21.5
        self.employee = self.env.ref('hr.employee_hne')
        self.contract = self.env['hr.contract'].create({
            'name': 'Test',
            'employee_id': self.employee.id,
            'structure_type_id': self.env.ref('hr_payroll.structure_type_employee').id,
            'date_start': '2020-01-01',
            'resource_calendar_id': self.employee.resource_calendar_id.id,
            'wage': self.test_hourly_wage,
            'paid_hourly_attendance': True,
            'state': 'open',
        })
        self._setup_attendance(self.employee)
        self.payslip = self.env['hr.payslip'].create({
            'name': 'test slip',
            'employee_id': self.employee.id,
            'date_from': '2020-01-06',
            'date_to': '2020-01-19',
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

    def _getCategories(self):
        categories = defaultdict(float)
        for line in self.payslip.line_ids:
            category_id = line.category_id
            category_code = line.category_id.code
            while category_code:
                categories[category_code] += line.total
                category_id = category_id.parent_id
                category_code = category_id.code
        return categories

    def test_attendance_hourly(self):
        self.payslip._onchange_employee()
        self.assertTrue(self.payslip.contract_id, 'No auto-discovered contract!')
        self.payslip.compute_sheet()
        # 58.97 => 40hr regular, 18.97hr OT
        # 68.4  => 40hr regular, 28.4hr  OT
        # (80 * 21.50) + (47.37 * 21.50 * 1.5) = 3247.6825
        cats = self._getCategories()
        self.assertAlmostEqual(cats['BASIC'], 3247.68, 2)

        # ensure unlink behavior.
        self.payslip.attendance_ids = self.env['hr.attendance'].browse()
        self.payslip.state = 'draft'
        self.payslip.flush()
        self.payslip._onchange_employee()
        self.payslip.compute_sheet()
        cats = self._getCategories()
        self.assertAlmostEqual(cats['BASIC'], 3247.68, 2)

        self.payslip.write({'attendance_ids': [(5, 0, 0)]})
        self.payslip.state = 'draft'
        self.payslip.flush()
        self.payslip._onchange_employee()
        self.payslip.compute_sheet()
        cats = self._getCategories()
        self.assertAlmostEqual(cats['BASIC'], 3247.68, 2)
