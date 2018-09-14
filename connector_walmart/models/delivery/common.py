# © 2017,2018 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class DeliveryCarrier(models.Model):
    """ Adds Walmart specific fields to ``delivery.carrier``

    ``walmart_code``

        Code of the carrier delivery method in Walmart.
        Example: ``Standard``

    ``walmart_carrier_code``

        Walmart specific list of carriers.

    """
    _inherit = "delivery.carrier"

    walmart_code = fields.Selection(
        selection=[
            ('Value', 'Value'),
            ('Standard', 'Standard'),
            ('Express', 'Express'),
            ('Oneday', 'Oneday'),
            ('Freight', 'Freight'),
        ],
        string='Walmart Method Code',
        required=False,
    )

    # From API:
    # UPS, USPS, FedEx, Airborne, OnTrac, DHL, NG, LS, UDS, UPSMI, FDX
    walmart_carrier_code = fields.Selection(
        selection=[
            ('UPS', 'UPS'),
            ('USPS', 'USPS'),
            ('FedEx', 'FedEx'),
            ('Airborne', 'Airborne'),
            ('OnTrac', 'OnTrac'),
            ('DHL', 'DHL'),
            ('NG', 'NG'),
            ('LS', 'LS'),
            ('UDS', 'UDS'),
            ('UPSMI', 'UPSMI'),
            ('FDX', 'FDX'),
        ],
        string='Walmart Base Carrier Code',
        required=False,
    )
