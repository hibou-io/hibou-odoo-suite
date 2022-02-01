# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import  models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def amount_for_commission(self, commission=None):
        if commission and commission.rate_type == 'timesheet':
            timesheets = self.timesheet_ids.filtered(lambda ts: ts.employee_id == commission.employee_id)
            amount = 0.0
            for timesheet in timesheets:
                invoice_line = self.invoice_line_ids.filtered(lambda l: timesheet.so_line in l.sale_line_ids)
                if invoice_line:
                    unit_amount = timesheet.unit_amount
                    if 'work_billing_rate' in timesheet and timesheet.work_type_id:
                        unit_amount *= timesheet.work_billing_rate
                    amount += invoice_line.price_unit * unit_amount
            return amount
        return super().amount_for_commission(commission)
