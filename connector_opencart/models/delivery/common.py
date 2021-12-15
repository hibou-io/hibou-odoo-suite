# © 2019 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
