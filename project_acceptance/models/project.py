from odoo import api, fields, models


class Task(models.Model):
    _inherit = 'project.task'        
    task_acceptance = fields.Selection([('accept', 'Accepted'), ('decline', 'Decline'), ('feedback', 'Feedback Provided')],'Task Acceptance', tracking=True)
    

class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'
    requires_acceptance = fields.Boolean('Require Acceptance')
