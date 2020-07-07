from odoo import fields, models


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
