# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    work_billing_rate = fields.Float(related='work_type_id.timesheet_billing_rate', string='Billing Multiplier')
