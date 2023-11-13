from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    line_ids = fields.One2many('project.task.line', 'task_id', string='Todo List')
    subtask_count_done = fields.Integer(compute='_compute_subtask_count', string="Sub-task Done count")

    @api.depends('child_ids')
    def _compute_subtask_count(self):
        for task in self:
            subtasks = task._get_all_subtasks()
            task.subtask_count = len(subtasks)
            task.subtask_count_done = len(subtasks.filtered(lambda t: t.is_closed))
    
    def action_subtask(self):
        action = self.env.ref('project.action_view_all_task').sudo().read()[0]

        # display all subtasks of current task
        action['domain'] = [('id', 'child_of', self.id), ('id', '!=', self.id)]

        ctx = dict(self.env.context)
        ctx = {k: v for k, v in ctx.items() if not k.startswith('search_default_')}
        ctx.update({
            'default_name': self.env.context.get('name', self.name) + ':',
            'default_parent_id': self.id,  # will give default subtask field in `default_get`
            'default_company_id': self.env.company.id,
        })

        action['context'] = ctx

        return action


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

    @api.onchange('kanban_state')
    def _onchange_kanban_state(self):
        if self.kanban_state == 'done':
            self.user_id = self.env.user
