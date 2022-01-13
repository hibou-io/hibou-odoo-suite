# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # TODO We need MORE here...
    module_hr_payroll_payment = fields.Boolean(string='Payments & Advanced Accounting')
    module_hr_payroll_attendance = fields.Boolean(string='Attendance Entries & Overtime')
    module_hr_payroll_timesheet = fields.Boolean(string='Timesheet Entries & Overtime')
    module_hr_payroll_commission = fields.Boolean(string='Commission')
    module_l10n_us_hr_payroll = fields.Boolean(string='USA Payroll')
    module_l10n_us_hr_payroll_401k = fields.Boolean(string='USA Payroll 401k')

    payslip_sum_type = fields.Selection([
        ('date_from', 'Date From'),
        ('date_to', 'Date To'),
        ('date', 'Accounting Date'),
    ], 'Payslip Sum Behavior', help="Behavior for what payslips are considered "
                                    "during rule execution.  Stock Odoo behavior "
                                    "would not consider a payslip starting on 2019-12-30 "
                                    "ending on 2020-01-07 when summing a 2020 payslip category.\n\n"
                                    "Accounting Date requires Payroll Accounting and will "
                                    "fall back to date_to as the 'closest behavior'.",
                               config_parameter='hr_payroll.payslip.sum_behavior')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('hr_payroll.payslip.sum_behavior',
                                                  self.payslip_sum_type or 'date_from')
