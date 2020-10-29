from datetime import date
from logging import getLogger
from urllib.request import urlopen
from suds import WebFault

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from .api.config import StampsConfiguration
from .api.services import StampsService

_logger = getLogger(__name__)

STAMPS_PACKAGE_TYPES = [
    'Unknown',
    'Postcard',
    'Letter',
    'Large Envelope or Flat',
    'Thick Envelope',
    'Package',
    'Flat Rate Box',
    'Small Flat Rate Box',
    'Large Flat Rate Box',
    'Flat Rate Envelope',
    'Flat Rate Padded Envelope',
    'Large Package',
    'Oversized Package',
    'Regional Rate Box A',
    'Regional Rate Box B',
    'Legal Flat Rate Envelope',
    'Regional Rate Box C',
]

STAMPS_INTEGRATION_ID = 'f62cb4f0-aa07-4701-a1dd-f0e7c853ed3c'

class ProductPackaging(models.Model):
    _inherit = 'product.packaging'

    package_carrier_type = fields.Selection(selection_add=[('stamps', 'Stamps.com')])
    stamps_cubic_pricing = fields.Boolean(string="Stamps.com Use Cubic Pricing")


class ProviderStamps(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('stamps', 'Stamps.com (USPS)')])

    stamps_username = fields.Char(string='Stamps.com Username', groups='base.group_system')
    stamps_password = fields.Char(string='Stamps.com Password', groups='base.group_system')

    stamps_service_type = fields.Selection([('US-FC', 'First-Class'),
                                            ('US-PM', 'Priority'),
                                            ],
                                           required=True, string="Service Type", default="US-PM")
    stamps_default_packaging_id = fields.Many2one('product.packaging', string='Default Package Type')

    stamps_image_type = fields.Selection([('Auto', 'Auto'),
                                          ('Png', 'PNG'),
                                          ('Gif', 'GIF'),
                                          ('Pdf', 'PDF'),
                                          ('Epl', 'EPL'),
                                          ('Jpg', 'JPG'),
                                          ('PrintOncePdf', 'Print Once PDF'),
                                          ('EncryptedPngUrl', 'Encrypted PNG URL'),
                                          ('Zpl', 'ZPL'),
                                          ('AZpl', 'AZPL'),
                                          ('BZpl', 'BZPL'),
                                          ],
                                         required=True, string="Image Type", default="Pdf")

    def _stamps_package_type(self, package=None):
        if not package:
            return self.stamps_default_packaging_id.shipper_package_code
        return package.packaging_id.shipper_package_code if package.packaging_id.shipper_package_code in STAMPS_PACKAGE_TYPES else 'Package'

    def _stamps_package_is_cubic_pricing(self, package=None):
        if not package:
            return self.stamps_default_packaging_id.stamps_cubic_pricing
        return package.packaging_id.stamps_cubic_pricing

    def _stamps_package_dimensions(self, package=None):
        if not package:
            package_type = self.stamps_default_packaging_id
        else:
            package_type = package.packaging_id
        return package_type.length, package_type.width, package_type.height

    def _get_stamps_service(self):
        sudoself = self.sudo()
        config = StampsConfiguration(integration_id=STAMPS_INTEGRATION_ID,
                                     username=sudoself.stamps_username,
                                     password=sudoself.stamps_password,
                                     wsdl=('testing' if not sudoself.prod_environment else None))
        return StampsService(configuration=config)

    def _stamps_convert_weight(self, weight):
        """ weight always expressed in database units (KG/LBS) """
        if self.stamps_default_packaging_id.max_weight and self.stamps_default_packaging_id.max_weight < weight:
            raise ValidationError('Stamps cannot ship for weight: ' + str(weight) + ' kgs/lbs.')

        get_param = self.env['ir.config_parameter'].sudo().get_param
        product_weight_in_lbs_param = get_param('product.weight_in_lbs')
        if product_weight_in_lbs_param == '1':
            return weight

        weight_in_pounds = weight * 2.20462
        return weight_in_pounds

    def _get_stamps_shipping_for_order(self, service, order, date_planned):
        weight = sum([(line.product_id.weight * line.product_qty) for line in order.order_line]) or 0.0
        weight = self._stamps_convert_weight(weight)

        if not all((order.warehouse_id.partner_id.zip, order.partner_shipping_id.zip)):
            raise ValidationError('Stamps needs ZIP. From: ' + str(order.warehouse_id.partner_id.zip) + ' To: ' + str(order.partner_shipping_id.zip))

        ret_val = service.create_shipping()
        ret_val.ShipDate = date_planned.strftime('%Y-%m-%d') if date_planned else date.today().isoformat()
        ret_val.FromZIPCode = self.get_shipper_warehouse(order=order).zip
        ret_val.ToZIPCode = order.partner_shipping_id.zip
        ret_val.PackageType = self._stamps_package_type()
        ret_val.ServiceType = self.stamps_service_type
        ret_val.WeightLb = weight
        ret_val.ContentType = 'Merchandise'
        return ret_val

    def _stamps_get_addresses_for_picking(self, picking):
        company = self.get_shipper_company(picking=picking)
        from_ = self.get_shipper_warehouse(picking=picking)
        to = self.get_recipient(picking=picking)
        return company, from_, to

    def _stamps_get_shippings_for_picking(self, service, picking):
        ret = []
        company, from_partner, to_partner = self._stamps_get_addresses_for_picking(picking)
        if not all((from_partner.zip, to_partner.zip)):
            raise ValidationError('Stamps needs ZIP. From: ' + str(from_partner.zip) + ' To: ' + str(to_partner.zip))

        for package in picking.package_ids:
            weight = self._stamps_convert_weight(package.shipping_weight)
            l, w, h = self._stamps_package_dimensions(package=package)

            ret_val = service.create_shipping()
            ret_val.ShipDate = date.today().isoformat()
            ret_val.FromZIPCode = from_partner.zip
            ret_val.ToZIPCode = to_partner.zip
            ret_val.PackageType = self._stamps_package_type(package=package)
            ret_val.CubicPricing = self._stamps_package_is_cubic_pricing(package=package)
            ret_val.Length = l
            ret_val.Width = w
            ret_val.Height = h
            ret_val.ServiceType = self.stamps_service_type
            ret_val.WeightLb = weight
            ret_val.ContentType = 'Merchandise'
            ret.append((package.name + ret_val.ShipDate + str(ret_val.WeightLb), ret_val))
        if not ret:
            weight = self._stamps_convert_weight(picking.shipping_weight)
            l, w, h = self._stamps_package_dimensions()

            ret_val = service.create_shipping()
            ret_val.ShipDate = date.today().isoformat()
            ret_val.FromZIPCode = from_partner.zip
            ret_val.ToZIPCode = to_partner.zip
            ret_val.PackageType = self._stamps_package_type()
            ret_val.CubicPricing = self._stamps_package_is_cubic_pricing()
            ret_val.Length = l
            ret_val.Width = w
            ret_val.Height = h
            ret_val.ServiceType = self.stamps_service_type
            ret_val.WeightLb = weight
            ret_val.ContentType = 'Merchandise'
            ret.append((picking.name + ret_val.ShipDate + str(ret_val.WeightLb), ret_val))

        return ret

    def stamps_get_shipping_price_from_so(self, orders):
        res = self.stamps_get_shipping_price_for_plan(orders, date.today().isoformat())
        return map(lambda r: r[0] if r else 0.0, res)

    def stamps_get_shipping_price_for_plan(self, orders, date_planned):
        res = []
        service = self._get_stamps_service()

        for order in orders:
            shipping = self._get_stamps_shipping_for_order(service, order, date_planned)
            rates = service.get_rates(shipping)
            if rates and len(rates) >= 1:
                rate = rates[0]
                price = float(rate.Amount)

                if order.currency_id.name != 'USD':
                    quote_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                    price = quote_currency.compute(rate.Amount, order.currency_id)

                delivery_days = rate.DeliverDays
                if delivery_days.find('-') >= 0:
                    delivery_days = delivery_days.split('-')
                    transit_days = int(delivery_days[-1])
                else:
                    transit_days = int(delivery_days)
                date_delivered = None
                if date_planned and transit_days > 0:
                    date_delivered = self.calculate_date_delivered(date_planned, transit_days)

                res = res + [(price, transit_days, date_delivered)]
                continue
            res = res + [(0.0, 0, None)]
        return res

    def stamps_rate_shipment(self, order):
        self.ensure_one()
        result = {
            'success': False,
            'price': 0.0,
            'error_message': 'Error Retrieving Response from Stamps.com',
            'warning_message': False
        }
        date_planned = None
        if self.env.context.get('date_planned'):
            date_planned = self.env.context.get('date_planned')
        rate = self.stamps_get_shipping_price_for_plan(order, date_planned)
        if rate:
            price, transit_time, date_delivered = rate[0]
            result.update({
                'success': True,
                'price': price,
                'error_message': False,
                'transit_time': transit_time,
                'date_delivered': date_delivered,
            })
            return result
        return result

    def stamps_send_shipping(self, pickings):
        res = []
        service = self._get_stamps_service()

        for picking in pickings:
            package_labels = []

            shippings = self._stamps_get_shippings_for_picking(service, picking)
            company, from_partner, to_partner = self._stamps_get_addresses_for_picking(picking)

            from_address = service.create_address()
            from_address.FullName = company.name
            from_address.Address1 = from_partner.street
            if from_partner.street2:
                from_address.Address2 = from_partner.street2
            from_address.City = from_partner.city
            from_address.State = from_partner.state_id.code
            from_address = service.get_address(from_address).Address

            to_address = service.create_address()
            to_address.FullName = to_partner.name
            to_address.Address1 = to_partner.street
            if to_partner.street2:
                to_address.Address2 = to_partner.street2
            to_address.City = to_partner.city
            to_address.State = to_partner.state_id.code
            to_address = service.get_address(to_address).Address

            try:
                for txn_id, shipping in shippings:
                    rates = service.get_rates(shipping)
                    if rates and len(rates) >= 1:
                        rate = rates[0]
                        shipping.Amount = rate.Amount
                        shipping.ServiceType = rate.ServiceType
                        shipping.DeliverDays = rate.DeliverDays
                        shipping.DimWeighting = rate.DimWeighting
                        shipping.Zone = rate.Zone
                        shipping.RateCategory = rate.RateCategory
                        shipping.ToState = rate.ToState
                        add_on = service.create_add_on()
                        add_on.AddOnType = 'US-A-DC'
                        add_on2 = service.create_add_on()
                        add_on2.AddOnType = 'SC-A-HP'
                        shipping.AddOns.AddOnV15 = [add_on, add_on2]
                        extended_postage_info = service.create_extended_postage_info()
                        if self.is_amazon(picking=picking):
                            extended_postage_info.bridgeProfileType = 'Amazon MWS'
                        label = service.get_label(from_address, to_address, shipping,
                                                  transaction_id=txn_id, image_type=self.stamps_image_type,
                                                  extended_postage_info=extended_postage_info)
                        package_labels.append((txn_id, label))
            except WebFault as e:
                _logger.warn(e)
                if package_labels:
                    for name, label in package_labels:
                        body = 'Cancelling due to error: ' + str(label.TrackingNumber)
                        try:
                            service.remove_label(label.TrackingNumber)
                        except WebFault as e:
                            raise ValidationError(e)
                        else:
                            picking.message_post(body=body)
                    raise ValidationError('Error on full shipment.  Attempted to cancel any previously shipped.')
                raise ValidationError('Error on shipment. ' + str(e))
            else:
                carrier_price = 0.0
                tracking_numbers = []
                for name, label in package_labels:
                    body = 'Shipment created into Stamps.com <br/> <b>Tracking Number : <br/>' + label.TrackingNumber + '</b>'
                    tracking_numbers.append(label.TrackingNumber)
                    carrier_price += float(label.Rate.Amount)
                    url = label.URL

                    response = urlopen(url)
                    attachment = response.read()
                    picking.message_post(body=body, attachments=[('LabelStamps-%s.%s' % (label.TrackingNumber, self.stamps_image_type), attachment)])
                shipping_data = {'exact_price': carrier_price, 'tracking_number': ','.join(tracking_numbers)}
                res = res + [shipping_data]
        return res

    def stamps_get_tracking_link(self, pickings):
        res = []
        for picking in pickings:
            ref = picking.carrier_tracking_ref
            res = res + ['https://tools.usps.com/go/TrackConfirmAction_input?qtc_tLabels1=%s' % ref]
        return res

    def stamps_cancel_shipment(self, picking):
        service = self._get_stamps_service()
        try:
            service.remove_label(picking.carrier_tracking_ref)
            picking.message_post(body=_(u'Shipment N° %s has been cancelled' % picking.carrier_tracking_ref))
            picking.write({'carrier_tracking_ref': '',
                           'carrier_price': 0.0})
        except WebFault as e:
            raise ValidationError(e)
