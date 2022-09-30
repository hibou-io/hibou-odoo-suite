from odoo import api, fields, models


class ProjectProjectStage(models.Model):
    _inherit = 'project.project.stage'

    requires_acceptance = fields.Boolean('Require Acceptance')

class ProjectTask(models.Model):
    _inherit = 'project.task'    
    
    task_acceptance = fields.Selection([('accept', 'Accepted'), ('decline', 'Decline'), ('feedback', 'Feedback Provided')],'Task Acceptance', traking=True)
    