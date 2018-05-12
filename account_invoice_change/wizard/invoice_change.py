from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InvoiceChangeWizard(models.TransientModel):
    _name = 'account.invoice.change'
    _description = 'Invoice Change'

    invoice_id = fields.Many2one('account.invoice', string='Invoice', readonly=True, required=True)
    invoice_company_id = fields.Many2one('res.company', readonly=True, related='invoice_id.company_id')
    user_id = fields.Many2one('res.users', string='Salesperson')
    date = fields.Date(string='Accounting Date')

    @api.model
    def default_get(self, fields):
        rec = super(InvoiceChangeWizard, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')

        # Checks on context parameters
        if not active_model or not active_ids:
            raise UserError(
                _("Programmation error: wizard action executed without active_model or active_ids in context."))
        if active_model != 'account.invoice':
            raise UserError(_(
                "Programmation error: the expected model for this action is 'account.invoice'. The provided one is '%d'.") % active_model)

        # Checks on received invoice records
        invoice = self.env[active_model].browse(active_ids)
        if len(invoice) != 1:
            raise UserError(_("Invoice Change expects only one invoice."))
        rec.update({
            'invoice_id': invoice.id,
            'user_id': invoice.user_id.id,
            'date': invoice.date,
        })
        return rec

    def _new_invoice_vals(self):
        vals = {}
        if self.invoice_id.user_id != self.user_id:
            vals['user_id'] = self.user_id.id
        if self.invoice_id.date != self.date:
            vals['date'] = self.date
        return vals

    @api.multi
    def affect_change(self):
        self.ensure_one()
        vals = self._new_invoice_vals()
        if vals:
            self.invoice_id.write(vals)
        if 'date' in vals and self.invoice_id.move_id:
            self.invoice_id.move_id.write({'date': vals['date']})
        return True
