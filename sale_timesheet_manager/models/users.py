from odoo import api, fields, models

from logging import getLogger as Logs
_logger = Logs(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _get_tasks_grouped_by_project(self):
        self.ensure_one()
        res = {}
        for task in self.env['project.task'].search([('user_id', '=', self.id)]):
            res.setdefault(task.project_id, []).append(task)
        _logger.warn('-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-')
        _logger.warn(res)
        return res
