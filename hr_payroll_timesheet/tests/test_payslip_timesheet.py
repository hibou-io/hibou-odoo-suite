# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo.addons.hr_payroll_hibou.tests import common
from odoo.exceptions import ValidationError


class TestPayslipTimesheet(common.TestPayslip):

    def setUp(self):
        super(TestPayslipTimesheet, self).setUp()

        self.work_type = self.env.ref('hr_timesheet_work_entry.work_input_timesheet')
        self.overtime_rules = self.work_type.overtime_type_id
        self.overtime_rules.hours_per_day = 0.0
        self.overtime_rules.multiplier = 1.5

        self.test_hourly_wage = 21.5
        self.employee = self._createEmployee()
        self.contract = self._createContract(self.employee,
                                             wage=self.test_hourly_wage,
                                             hourly_wage=self.test_hourly_wage,
                                             wage_type='hourly',
                                             paid_hourly_timesheet=True)

        self.work_entry_type_leave = self.env['hr.work.entry.type'].create({
            'name': 'Test PTO',
            'code': 'TESTPTO',
            'is_leave': True,
        })
        self.project = self.env['project.project'].create({
            'name': 'Timesheets',
        })

        # self.test_hourly_wage = 21.5
        # self.employee = self.env.ref('hr.employee_hne')
        # self.contract = self.env['hr.contract'].create({
        #     'name': 'Test',
        #     'employee_id': self.employee.id,
        #     'structure_type_id': self.env.ref('hr_payroll.structure_type_employee').id,
        #     'date_start': '2018-01-01',
        #     'resource_calendar_id': self.employee.resource_calendar_id.id,
        #     'wage': self.test_hourly_wage,
        #     'paid_hourly_timesheet': True,
        #     'state': 'open',
        # })
        # self.payslip_dummy = self.env['hr.payslip'].create({
        #     'name': 'test slip dummy',
        #     'employee_id': self.employee.id,
        #     'date_from': '2017-01-01',
        #     'date_to': '2017-01-31',
        # })
        # self.payslip = self.env['hr.payslip'].create({
        #     'name': 'test slip',
        #     'employee_id': self.employee.id,
        #     'date_from': '2018-01-01',
        #     'date_to': '2018-01-31',
        # })
        # self.project = self.env['project.project'].create({
        #     'name': 'Timesheets',
        # })
        # self.work_entry_type_leave = self.env['hr.work.entry.type'].create({
        #     'name': 'Test PTO',
        #     'code': 'TESTPTO',
        #     'is_leave': True,
        # })
        # self.leave_type = self.env['hr.leave.type'].create({
        #     'name': 'Test Paid Time Off',
        #     'time_type': 'leave',
        #     'allocation_type': 'no',
        #     'validity_start': False,
        #     'work_entry_type_id': self.work_entry_type_leave.id,
        # })


    def test_payslip_timesheet(self):
        self.assertTrue(self.contract.paid_hourly_timesheet)

        # Day 1
        self.env['account.analytic.line'].create({
            'employee_id': self.employee.id,
            'project_id': self.project.id,
            'date': '2018-01-01',
            'unit_amount': 5.0,
            'name': 'test',
        })
        self.env['account.analytic.line'].create({
            'employee_id': self.employee.id,
            'project_id': self.project.id,
            'date': '2018-01-01',
            'unit_amount': 3.0,
            'name': 'test',
        })

        # Day 2
        self.env['account.analytic.line'].create({
            'employee_id': self.employee.id,
            'project_id': self.project.id,
            'date': '2018-01-02',
            'unit_amount': 10.0,
            'name': 'test',
        })

        self.payslip_dummy = self._createPayslip(self.employee, '2017-01-01', '2017-01-31')
        # Make one that should be excluded.
        self.env['account.analytic.line'].create({
            'employee_id': self.employee.id,
            'project_id': self.project.id,
            'date': '2017-01-01',
            'unit_amount': 5.0,
            'name': 'test',
            'payslip_id': self.payslip_dummy.id,
        })

        self.payslip = self._createPayslip(self.employee, '2018-01-01', '2018-01-31')
        self.assertTrue(self.payslip.contract_id, 'No auto-discovered contract!')
        wage = self.test_hourly_wage
        self.assertTrue(self.payslip.worked_days_line_ids)

        timesheet_line = self.payslip.worked_days_line_ids.filtered(lambda l: l.code == 'TS')
        self.assertTrue(timesheet_line)
        self.assertEqual(timesheet_line.number_of_days, 2.0)
        self.assertEqual(timesheet_line.number_of_hours, 18.0)
        self.assertEqual(timesheet_line.amount, 18.0 * wage)

        # Day 3
        self.env['account.analytic.line'].create({
            'employee_id': self.employee.id,
            'project_id': self.project.id,
            'date': '2018-01-03',
            'unit_amount': 10.0,
            'name': 'test',
        })
        # Day 4
        self.env['account.analytic.line'].create({
            'employee_id': self.employee.id,
            'project_id': self.project.id,
            'date': '2018-01-04',
            'unit_amount': 10.0,
            'name': 'test',
        })
        # Day 5
        self.env['account.analytic.line'].create({
            'employee_id': self.employee.id,
            'project_id': self.project.id,
            'date': '2018-01-05',
            'unit_amount': 10.0,
            'name': 'test',
        })
        # Day 6
        self.env['account.analytic.line'].create({
            'employee_id': self.employee.id,
            'project_id': self.project.id,
            'date': '2018-01-06',
            'unit_amount': 4.0,
            'name': 'test',
        })

        self.payslip.state = 'draft'
        self.payslip.action_refresh_from_work_entries()
        timesheet_line = self.payslip.worked_days_line_ids.filtered(lambda l: l.code == 'TS')
        timesheet_overtime_line = self.payslip.worked_days_line_ids.filtered(lambda l: l.code == 'TS_OT')
        self.assertTrue(timesheet_line)
        self.assertEqual(timesheet_line.number_of_days, 5.0)
        self.assertEqual(timesheet_line.number_of_hours, 40.0)
        self.assertTrue(timesheet_overtime_line)
        self.assertEqual(timesheet_overtime_line.number_of_days, 1.0)
        self.assertEqual(timesheet_overtime_line.number_of_hours, 12.0)

    def test_payslip_timesheet_specific_work_entry_type(self):
        self.assertTrue(self.contract.paid_hourly_timesheet)
        worktype = self.env.ref('hr_timesheet_work_entry.work_input_timesheet_internal')

        # Day 1
        self.env['account.analytic.line'].create({
            'employee_id': self.employee.id,
            'project_id': self.project.id,
            'date': '2018-01-01',
            'unit_amount': 5.0,
            'name': 'test',
        })
        self.env['account.analytic.line'].create({
            'employee_id': self.employee.id,
            'project_id': self.project.id,
            'date': '2018-01-01',
            'unit_amount': 3.0,
            'name': 'test',
        })

        # Day 2
        self.env['account.analytic.line'].create({
            'employee_id': self.employee.id,
            'project_id': self.project.id,
            'date': '2018-01-02',
            'unit_amount': 10.0,
            'name': 'test',
            'work_type_id': worktype.id,
        })

        self.payslip_dummy = self._createPayslip(self.employee, '2017-01-01', '2017-01-31')
        # Make one that should be excluded.
        self.env['account.analytic.line'].create({
            'employee_id': self.employee.id,
            'project_id': self.project.id,
            'date': '2017-01-01',
            'unit_amount': 5.0,
            'name': 'test',
            'payslip_id': self.payslip_dummy.id,
        })

        self.payslip = self._createPayslip(self.employee, '2018-01-01', '2018-01-31')
        self.assertTrue(self.payslip.contract_id, 'No auto-discovered contract!')
        wage = self.test_hourly_wage
        self.assertTrue(self.payslip.worked_days_line_ids)

        timesheet_line = self.payslip.worked_days_line_ids.filtered(lambda l: l.code == 'TS')
        self.assertTrue(timesheet_line)
        self.assertEqual(timesheet_line.number_of_days, 1.0)
        self.assertEqual(timesheet_line.number_of_hours, 8.0)

        worktype_line = self.payslip.worked_days_line_ids.filtered(lambda l: l.code == worktype.code)
        self.assertTrue(worktype_line)
        self.assertEqual(worktype_line.number_of_days, 1.0)
        self.assertEqual(worktype_line.number_of_hours, 10.0)


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

        self.payslip = self._createPayslip(self.employee, '2020-01-06', '2020-01-19')
        self.assertTrue(self.payslip.worked_days_line_ids)

        leave_line = self.payslip.worked_days_line_ids.filtered(lambda l: l.code == 'TESTPTO')
        self.assertTrue(leave_line)
        self.assertEqual(leave_line.number_of_days, 1.0)
        self.assertEqual(leave_line.number_of_hours, 8.0)
        self.assertEqual(leave_line.amount, 8.0 * self.test_hourly_wage)
