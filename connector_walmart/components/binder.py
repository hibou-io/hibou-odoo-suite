# © 2017,2018 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class WalmartModelBinder(Component):
    """ Bind records and give odoo/walmart ids correspondence

    Binding models are models called ``walmart.{normal_model}``,
    like ``walmart.sale.order`` or ``walmart.product.product``.
    They are ``_inherits`` of the normal models and contains
    the Walmart ID, the ID of the Walmart Backend and the additional
    fields belonging to the Walmart instance.
    """
    _name = 'walmart.binder'
    _inherit = ['base.binder', 'base.walmart.connector']
    _apply_on = [
        'walmart.sale.order',
        'walmart.sale.order.line',
        'walmart.stock.picking',
    ]
