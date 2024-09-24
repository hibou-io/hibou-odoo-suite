from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    signifyd_fulfillment_method = fields.Selection(
        [
            ("DELIVERY", "Delivery"),
            ("COUNTER_PICKUP", "Counter Pickup"),
            ("CURBSIDE_PICKUP", "Curbside Pickup"),
            ("LOCKER_PICKUP", "Locker Pickup"),
            ("STANDARD_SHIPPING", "Standard Shipping"),
            ("EXPEDITED_SHIPPING", "Expedited Shipping"),
            ("GAS_PICKUP", "Gas Pickup"),
            ("SCHEDULED_DELIVERY", "Scheduled Delivery")
        ],
        string='Signifyd integration Fullfillment Method',
        default='STANDARD_SHIPPING'
    )
    # TODO add to view