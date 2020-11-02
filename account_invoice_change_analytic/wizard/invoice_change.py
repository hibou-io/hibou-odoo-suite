from odoo import api, fields, models, _


class InvoiceChangeWizard(models.TransientModel):
    _inherit = 'account.invoice.change'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    def _analytic_account_id(self, invoice):
        analytics = invoice.invoice_line_ids.mapped('account_analytic_id')
        if len(analytics):
            return analytics[0].id
        return False

    @api.model
    def default_get(self, fields):
        rec = super(InvoiceChangeWizard, self).default_get(fields)
        invoice = self.env['account.invoice'].browse(rec['invoice_id'])
        rec.update({
            'analytic_account_id': self._analytic_account_id(invoice),
        })
        return rec


    @api.multi
    def affect_change(self):
        old_analytic_id = self._analytic_account_id(self.invoice_id)
        res = super(InvoiceChangeWizard, self).affect_change()
        self._affect_analytic_change(old_analytic_id)
        return res

    def _affect_analytic_change(self, old_analytic_id):
        if old_analytic_id != self.analytic_account_id.id:
            self.invoice_id.invoice_line_ids \
                .filtered(lambda l: l.account_analytic_id.id == old_analytic_id) \
                .write({'account_analytic_id': self.analytic_account_id.id})
            if self.invoice_id.move_id:
                lines_to_affect = self.invoice_id.move_id \
                    .line_ids.filtered(lambda l: l.analytic_account_id.id == old_analytic_id)
                lines_to_affect.write({'analytic_account_id': self.analytic_account_id.id})
                lines_to_affect.create_analytic_lines()
