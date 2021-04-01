from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InvoiceChangeWizard(models.TransientModel):
    _name = 'account.invoice.change'
    _description = 'Invoice Change'

    move_id = fields.Many2one('account.move', string='Invoice', readonly=True, required=True)
    move_company_id = fields.Many2one('res.company', readonly=True, related='move_id.company_id')
    invoice_user_id = fields.Many2one('res.users', string='Salesperson')
    date = fields.Date(string='Accounting Date')
    invoice_date = fields.Date(string='Invoice Date')

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
        if active_model != 'account.move':
            raise UserError(_(
                "Programmation error: the expected model for this action is 'account.move'. The provided one is '%d'.") % active_model)

        # Checks on received invoice records
        invoice = self.env[active_model].browse(active_ids)
        if len(invoice) != 1:
            raise UserError(_("Invoice Change expects only one invoice."))
        rec.update({
            'move_id': invoice.id,
            'invoice_user_id': invoice.invoice_user_id.id,
            'date': invoice.date,
            'invoice_date': invoice.invoice_date,
        })
        return rec

    def _new_move_vals(self):
        vals = {}
        if self.move_id.invoice_user_id != self.invoice_user_id:
            vals['invoice_user_id'] = self.invoice_user_id.id
        if self.move_id.date != self.date:
            vals['date'] = self.date
        if self.move_id.invoice_date != self.invoice_date:
            vals['invoice_date'] = self.invoice_date
        return vals

    def affect_change(self):
        self.ensure_one()
        vals = self._new_move_vals()
        if vals:
            self.move_id.write(vals)
        return True
