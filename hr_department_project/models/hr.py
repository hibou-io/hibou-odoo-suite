from odoo import api, fields, models, _


class Department(models.Model):
    _inherit = 'hr.department'

    project_ids = fields.One2many('project.project', 'department_id', string='Projects')
    project_count = fields.Integer(compute='_compute_project_count', string='Project Count')

    def _compute_project_count(self):
        for department in self:
            department.project_count = len(department.with_context(active_test=False).project_ids)

    def project_tree_view(self):
        self.ensure_one()
        action = self.env.ref('project.open_view_project_all').read()[0]
        action['domain'] = [('department_id', '=', self.id)]
        action['context'] = {
            'default_department_id': self.id,
            'default_user_id': self.manager_id.id if self.manager_id else 0,
        }
        return action
