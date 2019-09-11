from odoo import api, fields, models


class Project(models.Model):
    _inherit = 'project.project'

    note = fields.Html(string='Note')

class ProjectTask(models.Model):
    _inherit = 'project.task'

    project_note = fields.Html(related='project_id.note')
