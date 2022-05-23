# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo.addons.sale_timesheet.tests.test_project_billing import TestProjectBilling


class TestSaleFlow(TestProjectBilling):

    # Mainly from test_billing_task_rate
    # Additional tests at the bottom.
    def test_billing_work_entry_rate(self):
        Task = self.env['project.task'].with_context(tracking_disable=True)
        Timesheet = self.env['account.analytic.line']

        # create a task
        task = Task.with_context(default_project_id=self.project_task_rate.id).create({
            'name': 'first task',
        })

        self.assertEqual(task.sale_line_id, self.so2_line_deliver_project_task, "Task created in a project billed on 'task rate' should be linked to a SOL containing a prepaid service product and the remaining hours of this SOL should be greater than 0.")
        self.assertEqual(task.partner_id, task.project_id.partner_id, "Task created in a project billed on 'task rate' should have the same customer as the one from the project")

        # log timesheet on task
        timesheet1 = Timesheet.create({
            'name': 'Test Line',
            'project_id': task.project_id.id,
            'task_id': task.id,
            'unit_amount': 50,
            'employee_id': self.employee_manager.id,
        })

        self.assertEqual(task.sale_line_id, timesheet1.so_line, "The timesheet should be linked to the SOL associated to the task since the pricing type of the project is task rate.")
        self.assertEqual(timesheet1.work_billing_amount, 50.0)

        # create a subtask
        subtask = Task.with_context(default_project_id=self.project_task_rate.id).create({
            'name': 'first subtask task',
            'parent_id': task.id,
            'display_project_id': self.project_subtask.id,
        })

        self.assertEqual(subtask.partner_id, subtask.parent_id.partner_id, "Subtask should have the same customer as the one from their mother")

        # log timesheet on subtask
        timesheet2 = Timesheet.create({
            'name': 'Test Line on subtask',
            'project_id': subtask.display_project_id.id,
            'task_id': subtask.id,
            'unit_amount': 50,
            'employee_id': self.employee_user.id,
        })
        self.assertEqual(subtask.display_project_id, timesheet2.project_id, "The timesheet is in the subtask project")
        self.assertFalse(timesheet2.so_line, "The timesheet should not be linked to SOL as it's a non billable project")

        # move task and subtask into task rate project
        task.write({
            'project_id': self.project_employee_rate.id,
        })
        subtask.write({
            'display_project_id': self.project_employee_rate.id,
        })

        self.assertEqual(task.sale_line_id, self.project_task_rate.sale_line_id, "Task moved in a employee rate billable project should keep its SOL because the partner_id has not changed too.")
        self.assertEqual(task.partner_id, self.project_task_rate.partner_id, "Task created in a project billed on 'employee rate' should have the same customer as the one from its initial project.")

        self.assertEqual(subtask.sale_line_id, subtask.parent_id.sale_line_id, "Subtask moved in a employee rate billable project should have the SOL of its parent since it keep its partner_id and this partner is different than the one in the destination project.")
        self.assertEqual(subtask.partner_id, subtask.parent_id.partner_id, "Subtask moved in a project billed on 'employee rate' should keep its initial customer, that is the one of its parent.")

        default_work_entry_type = self.env.ref('hr_timesheet_work_entry.work_input_timesheet')
        # Timesheets were for regular default 'Timesheet' type
        self.assertEqual((timesheet1 + timesheet2).mapped('work_type_id'), default_work_entry_type)
        # Line is set and total adds up to all of the timesheets.
        self.assertEqual(task.sale_line_id, self.so2_line_deliver_project_task)
        self.assertEqual(task.sale_line_id.qty_delivered, 50.0)

        double_rate_work_entry_type = self.env.ref('sale_timesheet_work_entry_rate.work_input_timesheet_double')
        self.assertEqual(double_rate_work_entry_type.timesheet_billing_rate, 2.0)

        # Convert to double rate.
        timesheet1.write({
            'work_type_id': double_rate_work_entry_type.id,
        })
        self.assertEqual(timesheet1.work_billing_amount, 100.0)
        self.assertEqual(task.sale_line_id.qty_delivered, 100.0)

        # Ensure that a created timesheet WITHOUT a work entry type behaves
        # the same as it would have before this module (e.g. for historic reasons)
        timesheet1.write({
            'work_type_id': False,
        })
        timesheet2.write({
            'work_type_id': False,
        })
        self.assertEqual(task.sale_line_id.qty_delivered, 50.0)

        # Ensure we can bill zero even with above default.
        zero_rate_work_entry_type = self.env.ref('sale_timesheet_work_entry_rate.work_input_timesheet_free')
        self.assertEqual(zero_rate_work_entry_type.timesheet_billing_rate, 0.0)

        timesheet1.write({
            'work_type_id': zero_rate_work_entry_type.id,
        })
        self.assertEqual(task.sale_line_id.qty_delivered, 0.0)
        self.assertEqual(timesheet1.work_billing_amount, 0.0)
