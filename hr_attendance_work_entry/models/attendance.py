from odoo import api, fields, models


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    work_type_id = fields.Many2one('hr.work.entry.type', string='Work Type',
                                   default=lambda self: self.env.ref('hr_attendance_work_entry.work_input_attendance',
                                                                     raise_if_not_found=False))

    @api.model
    def gather_attendance_work_types(self):
        work_types = self.env['hr.work.entry.type'].sudo().search([('allow_attendance', '=', True)])
        return work_types.read(['id', 'name', 'attendance_icon'])
