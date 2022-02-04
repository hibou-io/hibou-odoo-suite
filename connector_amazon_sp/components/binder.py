# © 2021 Hibou Corp.

from odoo.addons.component.core import Component


class AmazonModelBinder(Component):
    """ Bind records and give odoo/amazon ids correspondence

    Binding models are models called ``amazon.{normal_model}``,
    like ``amazon.sale.order`` or ``amazon.product.product``.
    They are ``_inherits`` of the normal models and contains
    the Amazon ID, the ID of the Amazon Backend and the additional
    fields belonging to the Amazon instance.
    """
    _name = 'amazon.binder'
    _inherit = ['base.binder', 'base.amazon.connector']
    _apply_on = [
        'amazon.product.product',
        'amazon.sale.order',
        'amazon.sale.order.line',
        'amazon.stock.picking',
    ]
