from odoo import api, fields, models

from logging import getLogger as Logs
_logger = Logs(__name__)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    time_manager_ids = fields.One2many('project.task.time.manager', 'task_id', string='Uncommitted time entries.')


class ProjectTaskTimeManager(models.Model):
    _name = 'project.task.time.manager'
    _description = 'Used to hold arbitrary data as o2m lines until it is committed via user or server action at EOD'

    # Relational Fields
    task_id = fields.Many2one('project.task', string='Parent Task')
    time_line_ids = fields.One2many('project.task.time.manager.line', 'time_manager_id')
    user_id = fields.Many2one('res.user', string='')


class ProjectTaskTimeManagerLine(models.Model):
    _name = 'project.task.time.manager.line'
    _description = 'Informational time lines that hold data until committed'

    # Relational Fields
    time_manager_id = fields.Many2one('project.task.time.manager')
    user_id = fields.Many2one('res.user', string='Timesheet User')

    # Informational Fields
    user_confirmed = fields.Boolean('User Confirmed Time')
    cron_confirmed = fields.Boolean('Cron Confirmed Time')

    date_start = fields.Date('Time Started')
    date_end = fields.Date('Time Finished')
    duration = fields.Float('Time Duration', compute='_compute_time_line_duration')

    def _compute_time_line_duration(self):
        for line in self:
            if line.date_start and line.date_end:
                time = line.date_start + line.date_end
                line.duration = float(time.hours)
            else:
                line.duration = 0
