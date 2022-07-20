from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    # payment_token_id = fields.Many2one('payment.token', string="Saved payment token",
    #                                    domain="[('acquirer_id.capture_manually', '=', False), ('company_id', '=', company_id)]",
    #                                    help="Note that tokens from acquirers set to only authorize transactions "
    #                                         "(instead of capturing the amount) are not available.")
    # company_id = fields.Many2one('res.company')  # technical requirement for acquirer domain
    # partner_id = fields.Many2one('res.partner')  # technical payment mode/token domain

    # amount = fields.Monetary('Amount')
    # so_amount_registered_payment = fields.Monetary(related='sale_order_id.manual_amount_registered_payment')
    so_amount_remaining = fields.Monetary(related='sale_order_id.manual_amount_remaining')
    # so_amount_over = fields.Boolean()

    # @api.onchange('amount')
    # def _compute_amount_remaining(self):
    #     self.so_amount_over = self.amount > self.so_amount_remaining

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
            # rec['so_amount_registered_payment'] = sale_order.manual_amount_registered_payment
            # rec['so_amount_remaining'] = sale_order.manual_amount_remaining
            # if 'amount' not in rec:
            #     rec['amount'] = sale_order.manual_amount_remaining
        # if 'company_id' not in rec:
        #     rec['company_id'] = sale_order.company_id.id
        # if 'partner_id' not in rec:
        #     rec['partner_id'] = sale_order.partner_id.id
        #     account_receivable = sale_order.partner_id.property_account_receivable_id
        #     if not account_receivable:
        #         raise UserError('Your partner must have an Account Receivable setup.')
        # if 'journal_id' not in rec:
        #     rec['journal_id'] = self.env['account.journal'].search([('company_id', '=', sale_order.company_id.id), ('type', 'in', ('bank', 'cash'))], limit=1).id
        # if 'payment_method_id' not in rec:
        #     domain = [('payment_type', '=', 'inbound')]
        #     rec['payment_method_id'] = self.env['account.payment.method'].search(domain, limit=1).id
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
        payment_vals = {
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
            # 'destination_account_id': self.line_ids[0].account_id.id
        }

        # if not self.currency_id.is_zero(self.payment_difference) and self.payment_difference_handling == 'reconcile':
        #     payment_vals['write_off_line_vals'] = {
        #         'name': self.writeoff_label,
        #         'amount': self.payment_difference,
        #         'account_id': self.writeoff_account_id.id,
        #     }
        return payment_vals
            
    def _create_payments(self):
        self.ensure_one()
        if not self.sale_order_id:
            return super(AccountPaymentRegister, self)._create_payments()
        payments = self.env['account.payment'].create(self._create_payment_vals_from_sale_order())
        payments.action_post()
        return payments

    # @api.onchange('partner_id', 'payment_method_id', 'journal_id')
    # def _onchange_set_payment_token_id(self):
    #     res = {}

    #     if not self.payment_method_id.code == 'electronic' or not self.partner_id or not self.journal_id:
    #         self.payment_token_id = False
    #         return res

    #     partners = self.partner_id | self.partner_id.commercial_partner_id | self.partner_id.commercial_partner_id.child_ids
    #     domain = [('partner_id', 'in', partners.ids), ('acquirer_id.journal_id', '=', self.journal_id.id)]
    #     self.payment_token_id = self.env['payment.token'].search(domain, limit=1)

    #     res['domain'] = {'payment_token_id': domain}
    #     return res

    # @api.onchange('journal_id', 'invoice_ids', 'sale_order_id')
    # def _onchange_journal(self):
    #     active_ids = self._context.get('active_ids')
    #     if self._context.get('active_model') != 'sale.order' or not active_ids:
    #         return super(AccountPaymentRegister, self)._onchange_journal()
    #     journal = self.journal_id
    #     if journal:
    #         domain_payment = [('payment_type', '=', 'inbound'), ('id', 'in', journal.inbound_payment_method_ids.ids)]
    #     return {'domain': {'payment_method_id': domain_payment}}

    # def _prepare_communication_sale_orders(self, sale_order):
    #     return " ".join(o.reference or o.name for o in sale_order)

    # def _prepare_payment_vals_sale_orders(self, sale_order):
    #     '''Create the payment values.

    #     :param sale_order: The sale orders to pay. In case of multiple
    #         documents.
    #     :return: The payment values as a dictionary.
    #     '''
    #     if self.amount <= 0:
    #         raise UserError("You must enter a positive amount.")
    #     elif self.amount > self.so_amount_remaining:
    #         raise UserError("You cannot make a payment for more than the difference of the total amount and existing "
    #                         "payments: %.2f" % self.so_amount_remaining)
    #     values = {
    #         'journal_id': self.journal_id.id,
    #         'payment_method_id': self.payment_method_id.id,
    #         'payment_date': self.payment_date,
    #         'communication': self._prepare_communication_sale_orders(sale_order),
    #         # TODO sale orders need to get to transactions somehow
    #         # 'invoice_ids': [(6, 0, invoices.ids)],
    #         'payment_type': 'inbound',  # if amount can be negative we need to allow this to be outbound
    #         'amount': self.amount,
    #         'currency_id': sale_order.currency_id.id,
    #         'partner_id': sale_order.partner_id.id,
    #         'partner_type': 'customer',
    #         'payment_token_id': self.payment_token_id.id,
    #     }
    #     return values

    # def get_payments_vals(self):
    #     if self.sale_order_id:
    #         return [self._prepare_payment_vals_sale_orders(self.sale_order_id)]
    #     return super(AccountPaymentRegister, self).get_payments_vals()

    # def create_payments(self):
    #     if self.sale_order_id:
    #         # user may not be able to create payment
    #         res = super(AccountPaymentRegister, self.sudo()).create_payments()
    #     else:
    #         res = super(AccountPaymentRegister, self).create_payments()
    #     if res and 'res_id' in res and self.sale_order_id:
    #         payment = self.env['account.payment'].browse(res['res_id'])
    #         self.sale_order_id.manual_payment_ids += payment
    #         if payment.name:  # if we don't have a name, then it started a transaction and that will be in chatter
    #             payment_link = payment._get_payment_chatter_link()
    #             for order in self.sale_order_id:
    #                 order.message_post(body=_('A %s payment has been registered: %s') % (payment.payment_method_code, payment_link))
    #         # return a 'dummy' action like object for tests
    #         return {'res_id': payment.id, 'res_model': payment._name}
    #     return res
