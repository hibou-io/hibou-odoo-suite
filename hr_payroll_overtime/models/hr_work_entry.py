from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .resource_calendar import WEEKDAY_SELECTION


class HRWorkEntryType(models.Model):
    _inherit = 'hr.work.entry.type'

    overtime_work_type_id = fields.Many2one('hr.work.entry.type', string='Overtime Work Type')
    overtime_type_id = fields.Many2one('hr.work.entry.overtime.type', string='Overtime Rules')


class HRWorkEntryOvertime(models.Model):
    _name = 'hr.work.entry.overtime.type'
    _description = 'Overtime Rules'

    name = fields.Char(string='Name')
    hours_per_day = fields.Float(string='Hours/Day',
                                 help='Number of hours worked in a single day to trigger overtime.')
    hours_per_week = fields.Float(string='Hours/Week',
                                  help='Number of hours worked in a week to trigger overtime.')
    multiplier = fields.Float(string='Multiplier',
                              help='Rate for when overtime is reached.')
    override_ids = fields.One2many('hr.work.entry.overtime.type.override', 'overtime_type_id',
                                   string='Overrides',
                                   help='Override lines with a Date will be considered before Day of Week.')

    def override_for_iso_date(self, iso_date):
        return self.override_ids.iso_date_applies(iso_date)


class HRWorkEntryOvertimeOverride(models.Model):
    _name = 'hr.work.entry.overtime.type.override'
    _description = 'Overtime Rule Override'
    _order = 'date desc, day_of_week'

    name = fields.Char(string='Description')
    overtime_type_id = fields.Many2one('hr.work.entry.overtime.type',
                                       string='Overtime Rules')
    work_type_id = fields.Many2one('hr.work.entry.type', string='Overtime Work Type', required=True,
                                   help='Distinct Work Type for this. Given the different rate, it should '
                                        ' be different from other Overtime Work Types (because payslips '
                                        'should only have one line/rate per work type).')
    multiplier = fields.Float(string='Multiplier',
                              help='Rate for when overtime is reached.')
    day_of_week = fields.Selection(WEEKDAY_SELECTION, string='Day of Week')
    date = fields.Date(string='Date')

    @api.constrains('day_of_week', 'date')
    def _constrain_days(self):
        for override in self:
            if override.day_of_week and override.date:
                raise ValidationError('An override should only have a Date OR Day of Week.')

    def iso_date_applies(self, iso_date):
        for override in self:
            if override.date and override.date.isocalendar() == iso_date:
                return override
            if int(override.day_of_week) == iso_date[2]:
                return override
