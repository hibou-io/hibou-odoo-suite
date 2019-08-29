from odoo import api, fields, models, _


class Project(models.Model):
    _inherit = 'project.project'

    department_id = fields.Many2one('hr.department', string='Department')
