from odoo import fields, models


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    work_type_id = fields.Many2one('hr.work.entry.type', string='Work Type',
                                   default=lambda self: self.env.ref('hr_attendance_work_entry.work_input_attendance',
                                                                     raise_if_not_found=False))
