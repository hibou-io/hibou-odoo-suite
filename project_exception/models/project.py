# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, models, fields, _
from odoo.exceptions import UserError


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
    def _reverse_field(self):
        return 'task_ids'

    def write(self, vals):
        if not vals.get('ignore_exception') and 'stage_id' in vals and 'project_id' not in vals:
            for task in self:
                if task.with_context(newVals=vals).detect_exceptions():
                    raise UserError(_('Exceptions were detected.'))
        res = super().write(vals)
        self.detect_exceptions()
        return res

    @api.model
    def _get_popup_action(self):
        return self.env.ref('project_exception.action_project_exception_confirm')
    
    def detect_exceptions(self):
        res = False
        if not self._context.get("skip_detect_exceptions"):
            self = self.with_context(skip_detect_exceptions=True)
            res = super(Task, self).detect_exceptions()
        return res
