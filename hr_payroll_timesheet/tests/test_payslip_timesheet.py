from odoo.tests import common
from odoo import fields


class TestPayslipTimesheet(common.TransactionCase):

    def setUp(self):
        super(TestPayslipTimesheet, self).setUp()
        self.employee = self.env['hr.employee'].create({
            'birthday': '1985-03-14',
            'country_id': self.ref('base.us'),
            'department_id': self.ref('hr.dep_rd'),
            'gender': 'male',
            'name': 'Jared'
        })
        self.contract = self.env['hr.contract'].create({
            'name': 'test',
            'employee_id': self.employee.id,
            'type_id': self.ref('hr_contract.hr_contract_type_emp'),
            'struct_id': self.ref('hr_payroll.structure_base'),
            'resource_calendar_id': self.ref('resource.resource_calendar_std'),
            'wage': 21.50,
            'date_start': '2018-01-01',
            'state': 'open',
            'paid_hourly_timesheet': True,
            'schedule_pay': 'monthly',
        })
        self.project = self.env['project.project'].create({
            'name': 'Timesheets',
        })

    def test_payslip_timesheet(self):
        self.assertTrue(self.contract.paid_hourly_timesheet)
        from_date = '2018-01-01'
        to_date = '2018-01-31'

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
            'unit_amount': 1.0,
            'name': 'test',
        })

        # Make one that should be excluded.
        self.env['account.analytic.line'].create({
            'employee_id': self.employee.id,
            'project_id': self.project.id,
            'date': '2017-01-01',
            'unit_amount': 5.0,
            'name': 'test',
        })

        # Create slip like a batch run.
        slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, self.employee.id, contract_id=False)
        res = {
            'employee_id': self.employee.id,
            'name': slip_data['value'].get('name'),
            'struct_id': slip_data['value'].get('struct_id'),
            'contract_id': slip_data['value'].get('contract_id'),
            'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
            'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
            'date_from': from_date,
            'date_to': to_date,
            'company_id': self.employee.company_id.id,
        }
        payslip = self.env['hr.payslip'].create(res)
        payslip.compute_sheet()
        self.assertTrue(payslip.worked_days_line_ids)

        timesheet_line = payslip.worked_days_line_ids.filtered(lambda l: l.code == 'TS')
        self.assertTrue(timesheet_line)
        self.assertEqual(timesheet_line.number_of_days, 2.0)
        self.assertEqual(timesheet_line.number_of_hours, 9.0)
