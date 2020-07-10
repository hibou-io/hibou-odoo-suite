from odoo import fields, models


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    payslip_id = fields.Many2one('hr.payslip', string="Payslip", readonly=True, ondelete='set null')

    def unlink(self):
        attn_with_payslip = self.filtered(lambda a: a.payslip_id)
        attn_with_payslip.write({'payslip_id': False})
        return super(HrAttendance, self - attn_with_payslip).unlink()
