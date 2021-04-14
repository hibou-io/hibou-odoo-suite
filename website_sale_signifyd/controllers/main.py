from odoo.http import request, route
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):

    @route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
    def payment_confirmation(self, **post):
        res = super(WebsiteSale, self).payment_confirmation()
        order_session_id = request.session.session_token
        checkout_token = request.session.session_token
        browser_ip_address = request.httprequest.environ['REMOTE_ADDR']
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            # Post completed order to Signifyd
            signifyd = request.env.company.signifyd_connector_id
            if signifyd:
                order.sudo().post_signifyd_case(order_session_id, checkout_token, browser_ip_address)

        return res
