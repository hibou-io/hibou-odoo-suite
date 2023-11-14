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
    user_id = fields.Many2one(
        'res.users', string='Completed By', 
        context={'active_test': False}, 
        compute='_compute_user_id', 
        store=True, readonly=False, precompute=True,
    )
    sequence = fields.Integer(string='Sequence')
    state = fields.Selection([
        ('done', 'Done'),
        ('blocked', 'Blocked'),
    ], string='State', copy=False)

    @api.depends('state')
    def _compute_user_id(self):
        for line in self.filtered(lambda l: l.state == 'done' and not l.user_id):
            line.user_id = self.env.user
