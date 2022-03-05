from odoo.http import request, route
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

    # Confirm order without taking payment
    @route(['/shop/confirm_without_payment'], type='http', auth='public', website=True)
    def confirm_without_payment(self, **post):
        order = request.website.sale_get_order()
        if not order:
            return request.redirect('/shop')
        if order.amount_due_today:
            return request.redirect('/shop/payment')

        # made it this far, lets confirm
        order.sudo().action_confirm()
        request.session['sale_last_order_id'] = order.id

        # cleans session/context
        # This should always exist, but it is possible to
        if request.website and request.website.sale_reset:
            request.website.sale_reset()
        return request.redirect('/shop/confirmation')

    def _update_website_sale_delivery_return(self, order, **post):
        res = super(WebsiteSalePaymentTerms, self)._update_website_sale_delivery_return(order, **post)
        Monetary = request.env['ir.qweb.field.monetary']
        currency = order.currency_id
        if order:
            res['amount_due_today'] = Monetary.value_to_html(order.amount_due_today, {'display_currency': currency})
            res['amount_due_today_raw'] = order.amount_due_today
        return res
