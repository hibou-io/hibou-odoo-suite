from datetime import timedelta

from odoo import api, fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_calendar_id = fields.Many2one(
        'resource.calendar', 'Delivery Calendar',
        help="This calendar represents days that the carrier will deliver the package.")

    # -------------------------- #
    # API for external providers #
    # -------------------------- #

    def get_shipping_price_for_plan(self, orders, date_planned):
        ''' For every sale order, compute the price of the shipment

        :param orders: A recordset of sale orders
        :param date_planned: Date to say that the shipment is leaving.
        :return list: A list of floats, containing the estimated price for the shipping of the sale order
        '''
        self.ensure_one()
        if hasattr(self, '%s_get_shipping_price_for_plan' % self.delivery_type):
            return getattr(self, '%s_get_shipping_price_for_plan' % self.delivery_type)(orders, date_planned)

    def calculate_transit_days(self, date_planned, date_delivered):
        self.ensure_one()
        if isinstance(date_planned, str):
            date_planned = fields.Datetime.from_string(date_planned)
        if isinstance(date_delivered, str):
            date_delivered = fields.Datetime.from_string(date_delivered)

        transit_days = 0
        while date_planned < date_delivered:
            if transit_days > 10:
                break
            interval = self.delivery_calendar_id.plan_days(1, date_planned, compute_leaves=True)

            if not interval:
                return self._calculate_transit_days_naive(date_planned, date_delivered)
            date_planned = interval[0][1]
            transit_days += 1

        if transit_days > 1:
            transit_days -= 1

        return transit_days

    def _calculate_transit_days_naive(self, date_planned, date_delivered):
        return abs((date_delivered - date_planned).days)

    def calculate_date_delivered(self, date_planned, transit_days):
        self.ensure_one()
        if isinstance(date_planned, str):
            date_planned = fields.Datetime.from_string(date_planned)

        # date calculations needs an extra day
        effective_transit_days = transit_days + 1

        interval = self.delivery_calendar_id.plan_days(effective_transit_days, date_planned, compute_leaves=True)
        if not interval:
            return self._calculate_date_delivered_naive(date_planned, transit_days)

        return fields.Datetime.to_string(interval[-1][1])

    def _calculate_date_delivered_naive(self, date_planned, transit_days):
        return fields.Datetime.to_string(date_planned + timedelta(days=transit_days))
