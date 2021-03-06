from odoo.http import request, route
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSalePaymentTerms(WebsiteSale):

    # In case payment_term_id is set by query-string in a link (from website_sale_delivery)
    @route(['/shop/payment'], type='http', auth="public", website=True)
    def payment(self, **post):
        order = request.website.sale_get_order()
        payment_term_id = post.get('payment_term_id')
        if order.amount_total <= request.website.payment_deposit_threshold:
            if payment_term_id:
                payment_term_id = int(payment_term_id)
            if order:
                order._check_payment_term_quotation(payment_term_id)
                if payment_term_id:
                    return request.redirect("/shop/payment")
        else:
            order.payment_term_id = False

        return super(WebsiteSalePaymentTerms, self).payment(**post)

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
            return {
                'payment_term_name': order.payment_term_id.name,
                'payment_term_id': order.payment_term_id.id,
                'note': order.payment_term_id.note,
                'require_payment': order.require_payment,
            }
        return {}

    @route(['/shop/reject_term_agreement'], type='http', auth='public', website=True)
    def reject_term_agreement(self, **kw):
        order = request.website.sale_get_order()
        if order:
            partner = request.env.user.partner_id
            order.write({'payment_term_id': request.website.sale_get_payment_term(partner),
                         'require_payment': True})
        return request.redirect('/shop/cart')

    # Confirm order without taking payment
    @route(['/shop/confirm_without_payment'], type='http', auth='public', website=True)
    def confirm_without_payment(self, **post):
        order = request.website.sale_get_order()
        if not order:
            return request.redirect('/shop')
        if order.require_payment:
            return request.redirect('/shop/payment')
        if not order.payment_term_id or (
                order.payment_term_id.deposit_percentage or order.payment_term_id.deposit_flat):
            return request.redirect('/shop/payment')

        # made it this far, lets confirm
        order.sudo().action_confirm()
        request.session['sale_last_order_id'] = order.id

        # cleans session/context
        # This should always exist, but it is possible to
        if request.website and request.website.sale_reset:
            request.website.sale_reset()
        return request.redirect('/shop/confirmation')
