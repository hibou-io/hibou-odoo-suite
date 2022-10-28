# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    timesheet_commission_rate = fields.Float(string='Timesheet Commission %',
                                             help='Rate to pay for invoiced timesheet value.')
