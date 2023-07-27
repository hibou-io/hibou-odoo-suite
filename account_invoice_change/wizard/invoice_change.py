from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InvoiceChangeWizard(models.TransientModel):
    _name = 'account.invoice.change'
    _description = 'Invoice Change'

    move_ids = fields.Many2many('account.move', string='Invoice', readonly=True, required=True)
    is_single_move = fields.Boolean(compute='_compute_move_company_id')
    move_company_id = fields.Many2one('res.company', readonly=True, compute='_compute_move_company_id')
    invoice_user_id = fields.Many2one('res.users', string='Salesperson')
    set_invoice_user_id = fields.Boolean()
    date = fields.Date(string='Accounting Date')
    set_date = fields.Boolean()
    invoice_date = fields.Date(string='Invoice Date')
    set_invoice_date = fields.Boolean()

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
        invoices = self.env[active_model].browse(active_ids)
        if invoices.filtered(lambda i: not i.is_invoice()):
            raise UserError(_('Only invoices can be updated.'))
        if invoices.filtered(lambda i: i.state in ('draft', 'cancel')):
            raise UserError(_('Only posted invoices can be updated.'))
        if len(invoices.company_id) > 1:
            raise UserError(_('Selected invoices must be in the same company.'))
        rec['move_ids'] = [(6, 0, invoices.ids)]
        if len(invoices) == 1:
            rec.update({
                'set_invoice_user_id': True,
                'set_date': True,
                'set_invoice_date': True,
                'invoice_user_id': invoices.invoice_user_id.id,
                'date': invoices.date,
                'invoice_date': invoices.invoice_date,
            })
        return rec
    
    @api.depends('move_ids')
    def _compute_move_company_id(self):
        for wiz in self:
            company = wiz.move_ids.company_id
            company.ensure_one()
            wiz.move_company_id = company
            wiz.is_single_move = len(wiz.move_ids) == 1

    def _new_move_vals(self):
        vals = {}
        if self.set_invoice_user_id:
            vals['invoice_user_id'] = self.invoice_user_id.id
        if self.set_date:
            vals['date'] = self.date
        if self.set_invoice_date:
            vals['invoice_date'] = self.invoice_date
        return vals

    def affect_change(self):
        self.ensure_one()
        vals = self._new_move_vals()
        if vals:
            self.move_ids.write(vals)
        return True
