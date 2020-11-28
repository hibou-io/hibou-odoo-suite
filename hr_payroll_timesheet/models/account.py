# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    payslip_id = fields.Many2one('hr.payslip', string="Payslip", ondelete='set null')

    @api.model_create_multi
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        payslips = self.env['hr.payslip'].sudo().browse([d.get('payslip_id', 0) for d in vals_list])
        if any(p.state not in ('draft', 'verify') for p in payslips.exists()):
            raise ValidationError('Cannot create attendance linked to payslip that is not draft.')
        return super().create(vals_list)

    def write(self, values):
        payslip_id = values.get('payslip_id')
        if payslip_id:
            payslip = self.env['hr.payslip'].sudo().browse(payslip_id)
            if payslip.exists().state not in ('draft', 'verify'):
                raise ValidationError('Cannot modify attendance linked to payslip that is not draft.')
        return super().write(values)

    def unlink(self):
        ts_with_payslip = self.filtered(lambda ts: ts.payslip_id)
        ts_with_payslip.write({'payslip_id': False})
        return super(AnalyticLine, self - ts_with_payslip).unlink()

