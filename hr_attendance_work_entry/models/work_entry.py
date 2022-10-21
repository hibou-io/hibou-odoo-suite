from odoo import fields, models


class HrWorkEntryType(models.Model):
    _inherit = 'hr.work.entry.type'
    _order = 'sequence, id'

    allow_attendance = fields.Boolean(string='Allow in Attendance')
    attendance_icon = fields.Char(string='Attendance Icon', default='fa-sign-in')
    attendance_state = fields.Selection([
        # ('checked_out', "Checked out"),  # reserved for detecting new punch in
        ('checked_in', "Checked in"),
        ('break', 'Break'),
        ('lunch', 'Lunch'),
    ], string='Attendance State', default='checked_in')
