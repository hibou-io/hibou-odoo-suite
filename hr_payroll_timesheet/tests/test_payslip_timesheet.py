from odoo.tests import common


class TestPayslipTimesheet(common.TransactionCase):

    def setUp(self):
        super(TestPayslipTimesheet, self).setUp()
        self.test_hourly_wage = 21.5
        self.employee = self.env.ref('hr.employee_hne')
        self.contract = self.env['hr.contract'].create({
            'name': 'Test',
            'employee_id': self.employee.id,
            'structure_type_id': self.env.ref('hr_payroll.structure_type_employee').id,
            'date_start': '2018-01-01',
            'resource_calendar_id': self.employee.resource_calendar_id.id,
            'wage': self.test_hourly_wage,
            'paid_hourly_timesheet': True,
            'state': 'open',
        })
        self.payslip_dummy = self.env['hr.payslip'].create({
            'name': 'test slip dummy',
            'employee_id': self.employee.id,
            'date_from': '2017-01-01',
            'date_to': '2017-01-31',
        })
        self.payslip = self.env['hr.payslip'].create({
            'name': 'test slip',
            'employee_id': self.employee.id,
            'date_from': '2018-01-01',
            'date_to': '2018-01-31',
        })
        self.project = self.env['project.project'].create({
            'name': 'Timesheets',
        })

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

        # Make one that should be excluded.
        self.env['account.analytic.line'].create({
            'employee_id': self.employee.id,
            'project_id': self.project.id,
            'date': '2017-01-01',
            'unit_amount': 5.0,
            'name': 'test',
            'payslip_id': self.payslip_dummy.id,
        })

        self.payslip._onchange_employee()
        self.assertTrue(self.payslip.contract_id, 'No auto-discovered contract!')
        wage = self.test_hourly_wage
        self.payslip.compute_sheet()
        self.assertTrue(self.payslip.worked_days_line_ids)

        timesheet_line = self.payslip.worked_days_line_ids.filtered(lambda l: l.code == 'TS')
        self.assertTrue(timesheet_line)
        self.assertEqual(timesheet_line.number_of_days, 2.0)
        self.assertEqual(timesheet_line.number_of_hours, 18.0)

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
        self.payslip._onchange_employee()
        timesheet_line = self.payslip.worked_days_line_ids.filtered(lambda l: l.code == 'TS')
        timesheet_overtime_line = self.payslip.worked_days_line_ids.filtered(lambda l: l.code == 'TS_OT')
        self.assertTrue(timesheet_line)
        self.assertEqual(timesheet_line.number_of_days, 5.0)
        self.assertEqual(timesheet_line.number_of_hours, 40.0)
        self.assertTrue(timesheet_overtime_line)
        self.assertEqual(timesheet_overtime_line.number_of_days, 1.0)
        self.assertEqual(timesheet_overtime_line.number_of_hours, 12.0)
