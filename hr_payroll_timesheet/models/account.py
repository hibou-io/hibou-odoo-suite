from odoo import fields, models


class AnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    payslip_id = fields.Many2one('hr.payslip', string="Payslip", readonly=True, ondelete='set null')

    def unlink(self):
        ts_with_payslip = self.filtered(lambda ts: ts.payslip_id)
        ts_with_payslip.write({'payslip_id': False})
        return super(AnalyticLine, self - ts_with_payslip).unlink()

