# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo.addons.sale_timesheet.tests.test_project_billing import TestProjectBilling


class TestSaleFlow(TestProjectBilling):

    # Mainly from test_billing_task_rate
    # Additional tests at the bottom.
    def test_billing_work_entry_rate(self):
        Task = self.env['project.task'].with_context(tracking_disable=True)
        Timesheet = self.env['account.analytic.line']

        # set subtask project on task rate project
        self.project_task_rate.write({'subtask_project_id': self.project_subtask.id})

        # create a task
        task = Task.with_context(default_project_id=self.project_task_rate.id).create({
            'name': 'first task',
            'partner_id': self.partner_customer_usd.id,
        })
        task._onchange_project()

        self.assertEqual(task.billable_type, 'task_rate', "Task in project 'task rate' should be billed at task rate")
        self.assertEqual(task.sale_line_id, self.project_task_rate.sale_line_id, "Task created in a project billed on 'task rate' should be linked to a SOL of the project")
        self.assertEqual(task.partner_id, task.project_id.partner_id, "Task created in a project billed on 'employee rate' should have the same customer as the one from the project")

        # log timesheet on task
        timesheet1 = Timesheet.create({
            'name': 'Test Line',
            'project_id': task.project_id.id,
            'task_id': task.id,
            'unit_amount': 50,
            'employee_id': self.employee_manager.id,
        })

        self.assertEqual(self.project_task_rate.sale_line_id, timesheet1.so_line, "The timesheet should be linked to the SOL associated to the Employee manager in the map")

        # create a subtask
        subtask = Task.with_context(default_project_id=self.project_task_rate.subtask_project_id.id).create({
            'name': 'first subtask task',
            'parent_id': task.id,
        })

        self.assertEqual(subtask.billable_type, 'task_rate', "Subtask in a non billable project with a so line set is task rate billable")
        self.assertEqual(subtask.project_id.billable_type, 'no', "The subtask project is non billable even if the subtask is")
        self.assertEqual(subtask.partner_id, subtask.parent_id.partner_id, "Subtask should have the same customer as the one from their mother")

        # log timesheet on subtask
        timesheet2 = Timesheet.create({
            'name': 'Test Line on subtask',
            'project_id': subtask.project_id.id,
            'task_id': subtask.id,
            'unit_amount': 50,
            'employee_id': self.employee_user.id,
        })

        self.assertEqual(subtask.project_id, timesheet2.project_id, "The timesheet is in the subtask project")
        self.assertEqual(timesheet2.so_line, subtask.sale_line_id, "The timesheet should be linked to SOL as the task even in a non billable project")

        # move task and subtask into task rate project
        task.write({
            'project_id': self.project_employee_rate.id,
        })
        task._onchange_project()
        subtask.write({
            'project_id': self.project_employee_rate.id,
        })
        subtask._onchange_project()

        self.assertEqual(task.billable_type, 'employee_rate', "Task moved in project 'employee rate' should be billed at employee rate")
        self.assertFalse(task.sale_line_id, "Task moved in a employee rate billable project have empty so line")
        self.assertEqual(task.partner_id, task.project_id.partner_id, "Task created in a project billed on 'employee rate' should have the same customer as the one from the project")

        self.assertEqual(subtask.billable_type, 'employee_rate', "subtask moved in project 'employee rate' should be billed at employee rate")
        self.assertFalse(subtask.sale_line_id, "Subask moved in a employee rate billable project have empty so line")
        self.assertEqual(subtask.partner_id, task.project_id.partner_id, "Subask created in a project billed on 'employee rate' should have the same customer as the one from the project")

        # Work Entry Type
        task.write({
            'project_id': self.project_task_rate.id,
        })
        task._onchange_project()
        subtask.write({
            'project_id': self.project_task_rate.id,
        })
        subtask._onchange_project()
        default_work_entry_type = self.env.ref('hr_timesheet_work_entry.work_input_timesheet')
        # Timesheets were for regular default 'Timesheet' type
        self.assertEqual((timesheet1 + timesheet2).mapped('work_type_id'), default_work_entry_type)
        # Line is set and total adds up to all of the timesheets.
        self.assertEqual(task.sale_line_id, self.so2_line_deliver_project_task)
        self.assertEqual(task.sale_line_id.qty_delivered, 100.0)

        double_rate_work_entry_type = self.env.ref('sale_timesheet_work_entry_rate.work_input_timesheet_double')
        self.assertEqual(double_rate_work_entry_type.timesheet_billing_rate, 2.0)

        # Convert to double rate.
        timesheet1.write({
            'work_type_id': double_rate_work_entry_type.id,
        })
        self.assertEqual(task.sale_line_id.qty_delivered, 150.0)
