# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    work_billing_rate = fields.Float(related='work_type_id.timesheet_billing_rate', string='Billing Multiplier')
    work_billing_amount = fields.Float(string='Billing Amount',
                                       compute='_compute_work_billing_amount', store=True)
    
    @api.depends('unit_amount', 'work_billing_rate')
    def _compute_work_billing_amount(self):
        for ts in self:
            ts.work_billing_amount = ts.unit_amount * \
                (ts.work_billing_rate if ts.work_type_id else 1.0)
