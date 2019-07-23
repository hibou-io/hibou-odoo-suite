from odoo import api, fields, models


class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def action_payslip_done(self):
        res = super(HRPayslip, self).action_payslip_done()
        if res and isinstance(res, (int, bool)):
            self.env['hr.leave.allocation'].payslip_update_accrual(self)
        return res
