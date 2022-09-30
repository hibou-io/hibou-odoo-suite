# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, models, fields


class ExceptionRule(models.Model):
    _inherit = 'exception.rule'

    model = fields.Selection(
        selection_add=[
            ('project.task', 'Task'),
        ],
        ondelete={
            'project.task': 'cascade',
        },
    )
    task_ids = fields.Many2many(
        'project.task',
        string="Task")


class Task(models.Model):
    _inherit = ['project.task', 'base.exception']
    _name = 'project.task'
    _order = 'main_exception_id asc, sequence, name, id'

    @api.model
    def create(self, values):
        res = super().create(values)
        res.detect_exceptions()
        return res

    @api.model
    def _exception_rule_eval_context(self, rec):
        res = super(Task, self)._exception_rule_eval_context(rec)
        res['task'] = rec
        return res

    @api.model
    def _reverse_field(self):
        return 'task_ids'

    def write(self, vals):
        if not vals.get('ignore_exception'):
            for task in self:
                if task.detect_exceptions():
                    return self._popup_exceptions()
        return super().write(vals)

    @api.model
    def _get_popup_action(self):
        return self.env.ref('project_exception.action_project_exception_confirm')
    
    def detect_exceptions(self):
        res = False
        if not self._context.get("detect_exceptions"):
            self = self.with_context(detect_exceptions=True)
            res = super(Task, self).detect_exceptions()
        return res
