# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MergeTimesheets(models.TransientModel):
    _inherit = 'hr_timesheet.merge.wizard'
    
    work_type_id = fields.Many2one('hr.work.entry.type', string='Work Type')
    
    @api.constrains('timesheet_ids')
    def _check_timesheet_ids(self):
        for wizard in self:
            if len(set(wizard.timesheet_ids.mapped('work_type_id'))) > 1:
                raise ValidationError('The timesheets must have the same work type.')
        super()._check_timesheet_ids()
    
    @api.model
    def default_get(self, fields_list):
        res = super(MergeTimesheets, self).default_get(fields_list)

        if 'timesheet_ids' in fields_list and res.get('timesheet_ids'):
            timesheets = self.env['account.analytic.line'].browse(res.get('timesheet_ids'))
            if timesheets and 'work_type_id' in fields_list:
                res['work_type_id'] = timesheets.mapped('work_type_id.id')[0]

        return res

    def action_merge(self):
        """
        super() (timesheet_grid.wizard.timesheet_merge_wizard.action_merge) is CLOSED
        to values injection. It is also closed to post-create modification because it 
        returns a closed window instead of an action with the new timesheet's id (e.g. a redirect)
        
        Thus a direct inline patch...
        """
        self.ensure_one()

        self.env['account.analytic.line'].create({
            'name': self.name,
            'date': self.date,
            'unit_amount': self.unit_amount,
            'encoding_uom_id': self.encoding_uom_id.id,
            'project_id': self.project_id.id,
            'task_id': self.task_id.id,
            'employee_id': self.employee_id.id,
            'work_type_id': self.work_type_id.id,
        })
        self.timesheet_ids.unlink()

        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("The timesheet entries have successfully been merged."),
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
