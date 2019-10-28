from odoo import http, fields
from odoo.addons.sale.controllers import product_configurator
from odoo.http import request


class ProductConfiguratorController(product_configurator.ProductConfiguratorController):
    @http.route(['/product_configurator/configure'], type='json', auth="user", methods=['POST'])
    def configure(self, product_id, pricelist_id, sale_line_id=None, **kw):
        add_qty = int(kw.get('add_qty', 1))
        product_template = request.env['product.template'].browse(int(product_id))

        to_currency = product_template.currency_id
        pricelist = self._get_pricelist(pricelist_id)
        if pricelist:
            product_template = product_template.with_context(pricelist=pricelist.id, partner=request.env.user.partner_id)
            to_currency = pricelist.currency_id

        sale_line = None
        if sale_line_id:
            sale_line = request.env['sale.order.line'].browse(int(sale_line_id))

        return request.env['ir.ui.view'].render_template("sale.product_configurator_configure", {
            'add_qty': add_qty,
            'product': product_template,
            'to_currency': to_currency,
            'pricelist': pricelist,
            'sale_line': sale_line,
            # get_attribute_exclusions deprecated, use product method
            'get_attribute_exclusions': self._get_attribute_exclusions,
            # get_attribute_value_defaults deprecated due to ecommerce templates
            'get_attribute_value_defaults': self._get_attribute_value_defaults,
        })

    def _get_attribute_value_defaults(self, product, sale_line, **kw):
        return product.get_default_attribute_values(sale_line)
