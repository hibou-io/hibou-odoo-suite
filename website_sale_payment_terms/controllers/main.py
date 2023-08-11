from odoo import tools, _
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.fields import Command
from odoo.http import request, route
from odoo.addons.payment.controllers import portal as payment_portal
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing
from odoo.addons.website_sale_delivery.controllers.main import WebsiteSaleDelivery


class WebsiteSalePaymentTerms(WebsiteSaleDelivery):

    def _get_shop_payment_values(self, order, **kwargs):
        values = super(WebsiteSalePaymentTerms, self)._get_shop_payment_values(order, **kwargs)
        values['amount'] = order.amount_due_today
        return values

    # In case payment_term_id is set by query-string in a link (from website_sale_delivery)
    @route('/shop/payment', type='http', auth='public', website=True, sitemap=False)
    def shop_payment(self, **post):
        order = request.website.sale_get_order()
        payment_term_id = post.get('payment_term_id')
        if payment_term_id:
            payment_term_id = int(payment_term_id)
        if order:
            order._check_payment_term_quotation(payment_term_id)
            if payment_term_id:
                return request.redirect("/shop/payment")
        return super(WebsiteSalePaymentTerms, self).shop_payment(**post)
    
    @route()
    def shop_payment_validate(self, sale_order_id=None, **post):
        """ 
        OVERRIDE: amount_total -> amount_due_today
        Method that should be called by the server when receiving an update
        for a transaction. State at this point :

         - UDPATE ME
        """
        if sale_order_id is None:
            order = request.website.sale_get_order()
            if not order and 'sale_last_order_id' in request.session:
                # Retrieve the last known order from the session if the session key `sale_order_id`
                # was prematurely cleared. This is done to prevent the user from updating their cart
                # after payment in case they don't return from payment through this route.
                last_order_id = request.session['sale_last_order_id']
                order = request.env['sale.order'].sudo().browse(last_order_id).exists()
        else:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            assert order.id == request.session.get('sale_last_order_id')

        tx = order.get_portal_last_transaction() if order else order.env['payment.transaction']

        if not order or (order.amount_due_today and not tx):
            return request.redirect('/shop')

        if order and not order.amount_due_today and not tx:
            order.with_context(send_email=True).action_confirm()
            return request.redirect(order.get_portal_url())

        # clean context and session, then redirect to the confirmation page
        request.website.sale_reset()
        if tx and tx.state == 'draft':
            return request.redirect('/shop')

        PaymentPostProcessing.remove_transactions(tx)
        return request.redirect('/shop/confirmation')

    # Main JS driven payment term updater.
    @route(['/shop/update_payment_term'], type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def update_order_payment_term(self, **post):
        order = request.website.sale_get_order()
        payment_term_id = int(post['payment_term_id'])
        try:
            if order:
                order._check_payment_term_quotation(payment_term_id)
            return self._update_website_payment_term_return(order, **post)
        except:
            return {'error': '[101] Unable to update payment terms.'}

    # Return values after order payment_term_id is updated
    def _update_website_payment_term_return(self, order, **post):
        if order:
            Monetary = request.env['ir.qweb.field.monetary']
            currency = order.currency_id
            return {
                'payment_term_name': order.payment_term_id.name,
                'payment_term_id': order.payment_term_id.id,
                'note': order.payment_term_id.note,
                'amount_due_today': order.amount_due_today,
                'amount_due_today_html': Monetary.value_to_html(order.amount_due_today, {'display_currency': currency}),
            }
        return {}

    @route(['/shop/reject_term_agreement'], type='http', auth='public', website=True)
    def reject_term_agreement(self, **kw):
        order = request.website.sale_get_order()
        if order:
            order.payment_term_id = False
        return request.redirect('/shop/cart')

    def _update_website_sale_delivery_return(self, order, **post):
        res = super(WebsiteSalePaymentTerms, self)._update_website_sale_delivery_return(order, **post)
        Monetary = request.env['ir.qweb.field.monetary']
        currency = order.currency_id
        if order:
            res['amount_due_today'] = Monetary.value_to_html(order.amount_due_today, {'display_currency': currency})
            res['amount_due_today_raw'] = order.amount_due_today
        return res


class PaymentPortal(payment_portal.PaymentPortal):
    
    @route()
    def shop_payment_transaction(self, order_id, access_token, **kwargs):
        """ Create a draft transaction and return its processing values.
        OVERRIDE: use order.amount_due_today instead of order.amount_total

        :param int order_id: The sales order to pay, as a `sale.order` id
        :param str access_token: The access token used to authenticate the request
        :param dict kwargs: Locally unused data passed to `_create_transaction`
        :return: The mandatory values for the processing of the transaction
        :rtype: dict
        :raise: ValidationError if the invoice id or the access token is invalid
        """
        # Check the order id and the access token
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token)
        except MissingError as error:
            raise error
        except AccessError:
            raise ValidationError(_("The access token is invalid."))

        if order_sudo.state == "cancel":
            raise ValidationError(_("The order has been canceled."))

        kwargs.update({
            'reference_prefix': None,  # Allow the reference to be computed based on the order
            'partner_id': order_sudo.partner_invoice_id.id,
            'sale_order_id': order_id,  # Include the SO to allow Subscriptions to tokenize the tx
        })
        kwargs.pop('custom_create_values', None)  # Don't allow passing arbitrary create values
        if not kwargs.get('amount'):
            kwargs['amount'] = order_sudo.amount_due_today

        if tools.float_compare(kwargs['amount'], order_sudo.amount_due_today, precision_rounding=order_sudo.currency_id.rounding):
            raise ValidationError(_("The cart has been updated. Please refresh the page."))

        tx_sudo = self._create_transaction(
            custom_create_values={'sale_order_ids': [Command.set([order_id])]}, **kwargs,
        )

        # Store the new transaction into the transaction list and if there's an old one, we remove
        # it until the day the ecommerce supports multiple orders at the same time.
        last_tx_id = request.session.get('__website_sale_last_tx_id')
        last_tx = request.env['payment.transaction'].browse(last_tx_id).sudo().exists()
        if last_tx:
            PaymentPostProcessing.remove_transactions(last_tx)
        request.session['__website_sale_last_tx_id'] = tx_sudo.id

        self._validate_transaction_for_order(tx_sudo, order_id)

        return tx_sudo._get_processing_values()
