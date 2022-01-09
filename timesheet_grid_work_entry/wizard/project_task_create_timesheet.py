# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import models, fields


class ProjectTaskCreateTimesheet(models.TransientModel):
    _inherit = 'project.task.create.timesheet'

    work_type_id = fields.Many2one('hr.work.entry.type', string='Work Type',
                                   default=lambda self: self.env.ref('hr_timesheet_work_entry.work_input_timesheet',
                                                                     raise_if_not_found=False))
    
    def save_timesheet(self):
        """
        super() (timesheet_grid.wizard.project_task_create_timesheet) 
        is CLOSED to values modification (builds internally)
        # It does however expose the created object, so at the cost of an 
        # additional write at flush we can just write here...
        """
        timesheets = super().save_timesheet()
        timesheets.write({
            'work_type_id': self.work_type_id.id,
        })
        return timesheets
