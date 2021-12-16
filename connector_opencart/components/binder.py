# © 2019-2021 Hibou Corp.

from odoo.addons.component.core import Component


class OpencartModelBinder(Component):
    """ Bind records and give odoo/opencart ids correspondence

    Binding models are models called ``opencart.{normal_model}``,
    like ``opencart.sale.order`` or ``opencart.product.product``.
    They are ``_inherits`` of the normal models and contains
    the Opencart ID, the ID of the Opencart Backend and the additional
    fields belonging to the Opencart instance.
    """
    _name = 'opencart.binder'
    _inherit = ['base.binder', 'base.opencart.connector']
    _apply_on = [
        'opencart.store',
        'opencart.sale.order',
        'opencart.sale.order.line',
        'opencart.stock.picking',
        'opencart.product.template',
        'opencart.product.template.attribute.value',
    ]
