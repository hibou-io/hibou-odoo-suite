from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    line_ids = fields.One2many('project.task.line', 'task_id', string='Todo List')


class ProjectTaskLine(models.Model):
    _name = 'project.task.line'
    _description = 'Task Todos'
    _order = 'sequence, id asc'

    task_id = fields.Many2one('project.task', required=True)
    name = fields.Char(string='Name')
    user_id = fields.Many2one('res.users', string='User')
    sequence = fields.Integer(string='Sequence')
    kanban_state = fields.Selection([
        ('normal', ''),
        ('done', 'Done'),
        ('blocked', 'Blocked')], string='State',
        copy=False, default='normal', required=True,
        help="A task's kanban state indicates special situations affecting it:\n"
             " * Blank is the default situation\n"
             " * Blocked indicates something is preventing the progress of this task\n"
             " * Done indicates the task is complete")

    # @api.onchange('kanban_state')
    # def _onchange_kanban_state(self):
    #     if self.kanban_state == 'done':
    #         self.user_id = self.env.user
