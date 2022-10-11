from odoo.addons.project.tests.test_access_rights import TestAccessRights


class TestProjectAcceptance(TestAccessRights):

    def test_10_task_aceptance(self):
        exception = self.env.ref('project_acceptance.except_no_project_id').sudo()
        exception.active = True

        task = self.create_task('Test task acceptance')
        self.assertTrue(task)
        self.assertFalse(task.task_acceptance)
        self.assertFalse(task.stage_id)

        #exception must exist if stage requires acceptance
        stage_in_progress = self.env['project.task.type'].search([('name', '=', 'In Progress')])
        self.assertEqual(stage_in_progress.name, 'In Progress')
        task.stage_id = stage_in_progress
        stage_in_progress.requires_acceptance = True
        stage_done = self.env['project.task.type'].search([('name', '=', 'Done')])
        self.assertTrue(task.exception_ids)
        self.assertEqual(task.stage_id.name, 'In Progress')
