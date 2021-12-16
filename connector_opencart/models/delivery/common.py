# © 2019-2021 Hibou Corp.

from odoo import models, fields, api


class DeliveryCarrier(models.Model):
    """ Adds Opencart specific fields to ``delivery.carrier``

    ``opencart_code``

        Code of the carrier delivery method in Opencart.
        Example: ``USPS``


    """
    _inherit = "delivery.carrier"

    opencart_code = fields.Char(
        string='Opencart Method Code',
        required=False,
    )
