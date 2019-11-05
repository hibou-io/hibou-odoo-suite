# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, models


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def compute_sheet(self):
        date = False
        if self.env.context.get('active_id'):
            date = self.env['hr.payslip.run'].browse(self.env.context.get('active_id')).date
        return super(HrPayslipEmployees, self.with_context(date=date)).compute_sheet()
