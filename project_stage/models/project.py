from odoo import api, fields, models, SUPERUSER_ID


class ProjectType(models.Model):
    _name = 'project.type'
    _description = 'Project Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    color = fields.Integer('Color Index')
    fold = fields.Boolean(string='Folded in Kanban',
        help='This stage is folded in the kanban view when there are no records in that stage to display.')


class Project(models.Model):
    _inherit = 'project.project'

    stage_id = fields.Many2one('project.type', string='Stage',
                               group_expand='_read_group_stage_ids', track_visibility='onchange', index=True)
    stage_color = fields.Integer(related='stage_id.color')

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)
