from odoo import api, exceptions, fields, models, _
from werkzeug.urls import url_encode

class ProjectTask(models.Model):
    _name = 'project.task'
    _inherit = ['project.task', 'portal.mixin']

    def preview_task(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }
