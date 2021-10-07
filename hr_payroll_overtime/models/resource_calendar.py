from odoo import fields, models


WEEKDAY_SELECTION = [
    ('1', 'Monday'),
    ('2', 'Tuesday'),
    ('3', 'Wednesday'),
    ('4', 'Thursday'),
    ('5', 'Friday'),
    ('6', 'Saturday'),
    ('7', 'Sunday'),
]


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    day_week_start = fields.Selection(WEEKDAY_SELECTION, string='Day Week Starts', required=True, default='1')
