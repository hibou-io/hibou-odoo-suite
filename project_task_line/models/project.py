from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    line_ids = fields.One2many('project.task.line', 'task_id', string='Todo List')
    subtask_count_done = fields.Integer(compute='_compute_subtask_count', string="Sub-task Done count")

    def _compute_subtask_count(self):
        for task in self:
            task.subtask_count = self.search_count([('id', 'child_of', task.id), ('id', '!=', task.id)])
            if task.subtask_count:
                task.subtask_count_done = self.search_count([('id', 'child_of', task.id), ('id', '!=', task.id),
                                                             ('stage_id.fold', '=', True)])
            else:
                task.subtask_count_done = 0


class ProjectTaskLine(models.Model):
    _name = 'project.task.line'
    _description = 'Task Todos'
    _order = 'sequence, id asc'

    task_id = fields.Many2one('project.task', required=True)
    name = fields.Char(string='Name')
    user_id = fields.Many2one('res.users', string='User')
    sequence = fields.Integer(string='Sequence')
    kanban_state = fields.Selection([
        ('normal', 'Grey'),
        ('done', 'Green'),
        ('blocked', 'Red')], string='Kanban State',
        copy=False, default='normal', required=True,
        help="A task's kanban state indicates special situations affecting it:\n"
             " * Grey is the default situation\n"
             " * Red indicates something is preventing the progress of this task\n"
             " * Green indicates the task is complete")

    @api.onchange('kanban_state')
    def _onchange_kanban_state(self):
        if self.kanban_state == 'done':
            self.user_id = self.env.user
