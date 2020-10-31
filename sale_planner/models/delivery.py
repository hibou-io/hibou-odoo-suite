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

    def rate_shipment_date_planned(self, order, date_planned=None):
        """
        For every sale order, compute the price of the shipment and potentially when it will arrive.
        :param order: `sale.order`
        :param date_planned: The date the shipment is expected to leave/be picked up by carrier.
        :return: rate in the same form the normal `rate_shipment` method does BUT
        -- Additional keys
        - transit_days: int
        - date_delivered: string
        """
        self.ensure_one()
        if hasattr(self, '%s_rate_shipment_date_planned' % self.delivery_type):
            # New API Odoo 11 - Carrier specific override.
            return getattr(self, '%s_rate_shipment_date_planned' % self.delivery_type)(order, date_planned)

        rate = self.with_context(date_planned=date_planned).rate_shipment(order)
        if rate and date_planned:
            if rate.get('date_delivered'):
                date_delivered = rate['date_delivered']
                transit_days = self.calculate_transit_days(date_planned, date_delivered)
                if not rate.get('transit_days') or transit_days < rate.get('transit_days'):
                    rate['transit_days'] = transit_days
            elif rate.get('transit_days'):
                rate['date_delivered'] = self.calculate_date_delivered(date_planned, rate.get('transit_days'))
        elif rate:
            date_delivered = rate.get('date_delivered')
            if date_delivered and not rate.get('transit_days'):
                # we could have a date delivered based on shipping it "now"
                # so we can still calculate the transit days
                rate['transit_days'] = self.calculate_transit_days(fields.Datetime.now(), date_delivered)
                rate.pop('date_delivered')  # because we don't have a date_planned, we cannot have a guarenteed delivery

        return rate

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

            current_date_planned = self.delivery_calendar_id.plan_days(1, date_planned, compute_leaves=True)
            if not current_date_planned:
                return self._calculate_transit_days_naive(date_planned, date_delivered)
            if current_date_planned == date_planned:
                date_planned += timedelta(days=1)
            else:
                date_planned = current_date_planned
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

        last_day = self.delivery_calendar_id.plan_days_end(effective_transit_days, date_planned, compute_leaves=True)
        if not last_day:
            return self._calculate_date_delivered_naive(date_planned, transit_days)

        return last_day

    def _calculate_date_delivered_naive(self, date_planned, transit_days):
        return date_planned + timedelta(days=transit_days)
