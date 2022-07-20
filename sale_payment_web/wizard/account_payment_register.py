from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    so_amount_remaining = fields.Monetary(related='sale_order_id.manual_amount_remaining')
    so_amount_over = fields.Boolean()

    @api.onchange('amount')
    def _compute_amount_remaining(self):
        self.so_amount_over = self.sale_order_id and self.amount > self.so_amount_remaining

    @api.model
    def default_get(self, fields):
        # super implementation checks active_ids, but not active_model
        active_ids = self._context.get('active_ids')
        if self._context.get('active_model') == 'sale.order' and 'line_ids' in fields:
            fields.remove('line_ids')
        rec = super(AccountPaymentRegister, self).default_get(fields)
        if self._context.get('active_model') != 'sale.order':
            return rec
        sale_order = self.env['sale.order'].browse(active_ids)
        if len(sale_order) != 1:
            raise UserError('Register payment must be called on a sale order.')

        if 'sale_order_id' not in rec:
            rec['sale_order_id'] = sale_order.id
        return rec
    
    def _compute_from_lines(self):
        wizards = self.filtered('sale_order_id')
        super(AccountPaymentRegister, self - wizards)._compute_from_lines()
        for wizard in wizards:
            sale_order = wizard.sale_order_id
            account_receivable = sale_order.partner_id.property_account_receivable_id
            if not account_receivable:
                raise UserError('Your partner must have an Account Receivable setup.')
            company = sale_order.company_id
            amount_currency = sale_order.manual_amount_remaining
            if sale_order.currency_id == company.currency_id:
                amount = amount_currency
            else:
                amount = sale_order.currency_id._convert(amount_currency, company.currency_id, company, fields.Date.context_today(self))
            wizard.update({
                'company_id': company.id,
                'partner_id': sale_order.partner_id.id,
                'partner_type': 'customer',
                'payment_type': 'inbound',
                'source_currency_id': sale_order.currency_id.id,
                'source_amount': amount,
                'source_amount_currency': amount_currency,
                'can_edit_wizard': True,
                'can_group_payments': False,
            })
    
    def _compute_communication(self):
        # The communication can't be computed in '_compute_from_lines' because
        # it's a compute editable field and then, should be computed in a separated method.    
        wizards = self.filtered('sale_order_id')
        super(AccountPaymentRegister, self - wizards)._compute_communication()
        for wizard in wizards:
            so = wizard.sale_order_id
            wizards.communication = so.reference or so.name
        
    def _compute_group_payment(self):
        wizards = self.filtered('sale_order_id')
        super(AccountPaymentRegister, self - wizards)._compute_group_payment()
        wizards.write({'group_payment': False})
        
    def _compute_journal_id(self):
        wizards = self.filtered('sale_order_id')
        super(AccountPaymentRegister, self - wizards)._compute_journal_id()
        for wizard in wizards:
            wizard.journal_id = self.env['account.journal'].search([
                    ('type', 'in', ('bank', 'cash')),
                    ('company_id', '=', wizard.company_id.id),
                ], limit=1)
        
    def _compute_available_partner_bank_ids(self):
        wizards = self.filtered('sale_order_id')
        super(AccountPaymentRegister, self - wizards)._compute_available_partner_bank_ids()
        for wizard in wizards:
            wizard.available_partner_bank_ids = wizard.journal_id.bank_account_id
    
    def _compute_partner_bank_id(self):
        wizards = self.filtered('sale_order_id')
        super(AccountPaymentRegister, self - wizards)._compute_partner_bank_id()
        wizards.write({'partner_bank_id': None})
    
    def _compute_suitable_payment_token_partner_ids(self):
        """ Override from `payment_fix_register_token` """
        wizards = self.filtered('sale_order_id')
        super(AccountPaymentRegister, self - wizards)._compute_suitable_payment_token_partner_ids()
        for wizard in wizards:
            partners = wizard.sale_order_id.partner_id
            commercial_partners = partners.commercial_partner_id
            children_partners = commercial_partners.child_ids
            wizard.suitable_payment_token_partner_ids = (partners + commercial_partners + children_partners)._origin
            
    def _create_payment_vals_from_sale_order(self):
        if self.amount <= 0:
            raise UserError("You must enter a positive amount.")
        elif self.amount > self.so_amount_remaining:
            raise UserError("You cannot make a payment for more than the difference of the total amount and existing "
                            "payments: %.2f" % self.so_amount_remaining)
        return {
            'date': self.payment_date,
            'amount': self.amount,
            'payment_type': self.payment_type,
            'partner_type': self.partner_type,
            'ref': self.communication,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'payment_method_id': self.payment_method_id.id,
            'sale_order_id': self.sale_order_id.id,
        }
            
    def _create_payments(self):
        self.ensure_one()
        if not self.sale_order_id:
            return super(AccountPaymentRegister, self)._create_payments()
        payments = self.env['account.payment'].create(self._create_payment_vals_from_sale_order())
        payments.action_post()
        return payments
