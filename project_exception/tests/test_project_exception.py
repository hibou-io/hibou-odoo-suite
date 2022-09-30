# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo.tests import common, Form


class TestProjectException(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.env = self.env(context=dict(self.env.context, tracking_disable=True))

    def test_project_task_creation_exception(self):
        exception = self.env.ref('project_exception.except_no_project_id')
        exception.active = True
        
        task = self.env['project.task'].create({
            'name': 'Test Task',
        })
        # Created exceptions on create.
        self.assertTrue(task.exception_ids)
        
        # Will return action on write, which may or not be followed.
        action = task.write({
            'name': 'Test Task - Test Written',
        })
        self.assertTrue(task.exception_ids)
        self.assertTrue(action)
        self.assertEqual(action.get('res_model'), 'project.exception.confirm')

        # Simulation the opening of the wizard task_exception_confirm and
        # set ignore_exception to True
        project_exception_confirm = Form(self.env[action['res_model']].with_context(action['context'])).save()
        project_exception_confirm.ignore = True
        project_exception_confirm.action_confirm()
        self.assertTrue(task.ignore_exception)
