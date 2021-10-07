# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo.addons.hr_payroll_account.models.hr_payroll_account import HrPayslip

# this is patched because this method is replaced in our implementation (and overridable via _generate_move())
def action_payslip_done(self):
    return super(HrPayslip, self).action_payslip_done()

HrPayslip.action_payslip_done = action_payslip_done
