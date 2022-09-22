# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    payslip_id = fields.Many2one('hr.payslip', string="Payslip", ondelete='set null')

    @api.model_create_multi
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        payslip_ids = [i for i in set([d.get('payslip_id') or 0 for d in vals_list]) if i != 0]
        if payslip_ids:
            payslips = self.env['hr.payslip'].sudo().browse(payslip_ids)
            if payslips.filtered(lambda p: p.state not in ('draft', 'verify')):
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
        attn_with_payslip = self.filtered(lambda a: a.payslip_id)
        attn_with_payslip.write({'payslip_id': False})
        return super(HrAttendance, self - attn_with_payslip).unlink()
