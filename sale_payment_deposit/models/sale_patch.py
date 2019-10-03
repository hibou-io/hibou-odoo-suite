from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.addons.sale.models.sale import SaleOrder


def _create_payment_transaction(self, vals):
    # This is a copy job from odoo.addons.sale.models.sale due to the closed nature of the vals.update(dict) call
    # Ultimately, only the 'vals.update' with the new amount is really used.
    '''Similar to self.env['payment.transaction'].create(vals) but the values are filled with the
    current sales orders fields (e.g. the partner or the currency).
    :param vals: The values to create a new payment.transaction.
    :return: The newly created payment.transaction record.
    '''
    # Ensure the currencies are the same.

    # extract variable for use later.
    sale = self[0]

    currency = sale.pricelist_id.currency_id
    if any([so.pricelist_id.currency_id != currency for so in self]):
        raise ValidationError(_('A transaction can\'t be linked to sales orders having different currencies.'))

    # Ensure the partner are the same.
    partner = sale.partner_id
    if any([so.partner_id != partner for so in self]):
        raise ValidationError(_('A transaction can\'t be linked to sales orders having different partners.'))

    # Try to retrieve the acquirer. However, fallback to the token's acquirer.
    acquirer_id = vals.get('acquirer_id')
    acquirer = False
    payment_token_id = vals.get('payment_token_id')

    if payment_token_id:
        payment_token = self.env['payment.token'].sudo().browse(payment_token_id)

        # Check payment_token/acquirer matching or take the acquirer from token
        if acquirer_id:
            acquirer = self.env['payment.acquirer'].browse(acquirer_id)
            if payment_token and payment_token.acquirer_id != acquirer:
                raise ValidationError(_('Invalid token found! Token acquirer %s != %s') % (
                payment_token.acquirer_id.name, acquirer.name))
            if payment_token and payment_token.partner_id != partner:
                raise ValidationError(_('Invalid token found! Token partner %s != %s') % (
                payment_token.partner.name, partner.name))
        else:
            acquirer = payment_token.acquirer_id

    # Check an acquirer is there.
    if not acquirer_id and not acquirer:
        raise ValidationError(_('A payment acquirer is required to create a transaction.'))

    if not acquirer:
        acquirer = self.env['payment.acquirer'].browse(acquirer_id)

    # Check a journal is set on acquirer.
    if not acquirer.journal_id:
        raise ValidationError(_('A journal must be specified of the acquirer %s.' % acquirer.name))

    if not acquirer_id and acquirer:
        vals['acquirer_id'] = acquirer.id

    # Override for Deposit
    amount = sum(self.mapped('amount_total'))
    # This is a patch, all databases will run this code even if this field doesn't exist.
    if hasattr(sale, 'amount_total_deposit') and sum(self.mapped('amount_total_deposit')):
        amount = sum(self.mapped('amount_total_deposit'))

    vals.update({
        'amount': amount,
        'currency_id': currency.id,
        'partner_id': partner.id,
        'sale_order_ids': [(6, 0, self.ids)],
    })

    transaction = self.env['payment.transaction'].create(vals)

    # Process directly if payment_token
    if transaction.payment_token_id:
        transaction.s2s_do_transaction()

    return transaction


# Patch core implementation.
SaleOrder._create_payment_transaction = _create_payment_transaction
