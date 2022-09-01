# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import hashlib
from datetime import date
from logging import getLogger
from urllib.request import urlopen
from suds import WebFault

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from .api.config import StampsConfiguration
from .api.services import StampsService

_logger = getLogger(__name__)

STAMPS_US_APO_FPO_STATE_CODES = (
    'AE',
    'AP',
    'AA',
)

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

STAMPS_CONTENT_TYPES = {
    'Letter': 'Document',
    'Postcard': 'Document',
}

STAMPS_INTEGRATION_ID = 'f62cb4f0-aa07-4701-a1dd-f0e7c853ed3c'


class StockPackageType(models.Model):
    _inherit = 'stock.package.type'

    package_carrier_type = fields.Selection(selection_add=[('stamps', 'Stamps.com')])
    stamps_cubic_pricing = fields.Boolean(string="Stamps.com Use Cubic Pricing")


class ProviderStamps(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('stamps', 'Stamps.com')],
                                     ondelete={'stamps': 'set default'})

    stamps_username = fields.Char(string='Stamps.com Username', groups='base.group_system')
    stamps_password = fields.Char(string='Stamps.com Password', groups='base.group_system')

    stamps_service_type = fields.Selection([('US-FC', 'USPS First-Class'),
                                            ('US-PM', 'USPS Priority'),
                                            ('US-XM', 'USPS Express'),
                                            ('US-MM', 'USPS Media Mail'),
                                            ('US-FCI', 'USPS First-Class International'),
                                            ('US-PMI', 'USPS Priority International'),
                                            ('US-EMI', 'USPS Express International'),
                                            ('SC-GPE', 'GlobalPost Economy'),
                                            ('SC-GPP', 'GlobalPost Standard'),
                                            ('SC-GPESS', 'GlobalPost SmartSaver Economy'),
                                            ('SC-GPPSS', 'GlobalPost SmartSaver Standard'),
                                            ],
                                           required=True, string="Service Type", default="US-PM")
    stamps_default_packaging_id = fields.Many2one('stock.package.type', string='Default Package Type')

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
                                         required=True, string="Image Type", default="Pdf",
                                         help='Generally PDF or ZPL are the great options.')
    stamps_addon_sc = fields.Boolean(string='Add Signature Confirmation')
    stamps_addon_dc = fields.Boolean(string='Add Delivery Confirmation')
    stamps_addon_hp = fields.Boolean(string='Add Hidden Postage')

    def _stamps_package_type(self, package=None):
        if not package:
            return self.stamps_default_packaging_id.shipper_package_code
        return package.package_type_id.shipper_package_code if package.package_type_id.shipper_package_code in STAMPS_PACKAGE_TYPES else 'Package'

    def _stamps_content_type(self, package=None):
        package_type = self._stamps_package_type(package=package)
        if package_type in STAMPS_CONTENT_TYPES:
            return STAMPS_CONTENT_TYPES[package_type]
        return 'Merchandise'

    def _stamps_package_is_cubic_pricing(self, package=None):
        if not package:
            return self.stamps_default_packaging_id.stamps_cubic_pricing
        return package.package_type_id.stamps_cubic_pricing

    def _stamps_package_dimensions(self, package=None):
        if not package:
            package_type = self.stamps_default_packaging_id
        else:
            package_type = package.package_type_id
        length_uom = self.env['product.template']._get_length_uom_id_from_ir_config_parameter()
        if length_uom.name == 'ft':
            return round(package_type.packaging_length / 12.0), round(package_type.width / 12.0), round(package_type.height / 12.0)
        elif length_uom.name == 'mm':
            return round(package_type.packaging_length * 0.0393701), round(package_type.width * 0.0393701), round(package_type.height * 0.0393701)
        return package_type.packaging_length, package_type.width, package_type.height

    def _get_stamps_service(self):
        sudoself = self.sudo()
        config = StampsConfiguration(integration_id=STAMPS_INTEGRATION_ID,
                                     username=sudoself.stamps_username,
                                     password=sudoself.stamps_password,
                                     wsdl=('testing' if not sudoself.prod_environment else None))
        return StampsService(configuration=config)

    def _stamps_convert_weight(self, weight):
        """ weight always expressed in database units (KG/LBS) """
        weight_uom = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        if weight_uom.name == 'kg':
            weight_in_pounds = weight * 2.20462
        else:
            weight_in_pounds = weight
        return weight_in_pounds

    def _get_stamps_shipping_for_order(self, service, order, date_planned):
        weight = sum([(line.product_id.weight * line.product_qty) for line in order.order_line]) or 0.0
        weight = self._stamps_convert_weight(weight)

        if not all((order.warehouse_id.partner_id.zip, order.partner_shipping_id.zip)):
            raise ValidationError(_('Stamps needs ZIP. From: "%s" To: "%s"',
                                  order.warehouse_id.partner_id.zip,
                                  order.partner_shipping_id.zip))

        ret_val = service.create_shipping()
        ret_val.ShipDate = date_planned.strftime('%Y-%m-%d') if date_planned else date.today().isoformat()
        shipper_partner = self.get_shipper_warehouse(order=order)
        ret_val.From = self._stamps_address(service, shipper_partner)
        ret_val.To = self._stamps_address(service, order.partner_shipping_id)
        ret_val.PackageType = self._stamps_package_type()
        ret_val.ServiceType = self.stamps_service_type
        ret_val.WeightLb = weight
        ret_val.ContentType = self._stamps_content_type()
        return ret_val

    def _get_stamps_shipping_multi(self, service, date_planned, order=False, picking=False, package=False):
        if order:
            weight = sum([(line.product_id.weight * line.product_qty) for line in order.order_line]) or 0.0
        elif not package:
            weight = picking.shipping_weight
        else:
            weight = package.shipping_weight or package.weight
        weight = self._stamps_convert_weight(weight)

        shipper = self.get_shipper_warehouse(order=order, picking=picking)
        recipient = self.get_recipient(order=order, picking=picking)

        if not all((shipper.zip, recipient.zip)):
            raise ValidationError(_('Stamps needs ZIP. From: "%s" To: "%s"',
                                  shipper.zip,
                                  recipient.zip))

        ret_val = service.create_shipping()
        ret_val.ShipDate = date_planned.strftime('%Y-%m-%d') if date_planned else date.today().isoformat()
        ret_val.From = self._stamps_address(service, shipper)
        ret_val.To = self._stamps_address(service, recipient)
        ret_val.PackageType = self._stamps_package_type(package=package)
        ret_val.WeightLb = weight
        ret_val.ContentType = 'Merchandise'
        return ret_val

    def _stamps_get_addresses_for_picking(self, picking):
        company = self.get_shipper_company(picking=picking)
        from_ = self.get_shipper_warehouse(picking=picking)
        to = self.get_recipient(picking=picking)
        return company, from_, to

    def _stamps_address(self, service, partner):
        address = service.create_address()
        if not partner.name or len(partner.name) < 2:
            raise ValidationError(_('Partner (%s) name must be more than 2 characters.', partner))
        address.FullName = partner.name
        address.Address1 = partner.street
        if partner.street2:
            address.Address2 = partner.street2
        address.City = partner.city
        address.State = partner.state_id.code
        if partner.country_id.code == 'US':
            zip_pieces = partner.zip.split('-')
            address.ZIPCode = zip_pieces[0]
            if len(zip_pieces) >= 2:
                address.ZIPCodeAddOn = zip_pieces[1]
        else:
            address.PostalCode = partner.zip or ''
        address.Country = partner.country_id.code
        res = service.get_address(address).Address
        return res

    def _stamps_hash_partner(self, partner):
        to_hash = ''.join(f[1] if isinstance(f, tuple) else str(f) for f in partner.read(['name', 'street', 'street2', 'city', 'country_id', 'state_id', 'zip', 'phone', 'email'])[0].values())
        return hashlib.sha1(to_hash.encode()).hexdigest()

    def _stamps_get_shippings_for_picking(self, service, picking):
        ret = []
        company, from_partner, to_partner = self._stamps_get_addresses_for_picking(picking)
        if not all((from_partner.zip, to_partner.zip)):
            raise ValidationError(_('Stamps needs ZIP. From: "%s" To: "%s"',
                                  from_partner.zip,
                                  to_partner.zip))

        picking_packages = picking.package_ids
        package_carriers = picking_packages.mapped('carrier_id')
        if package_carriers:
            # only ship ours
            picking_packages = picking_packages.filtered(lambda p: p.carrier_id == self and not p.carrier_tracking_ref)

        for package in picking_packages:
            weight = self._stamps_convert_weight(package.shipping_weight)
            l, w, h = self._stamps_package_dimensions(package=package)

            ret_val = service.create_shipping()
            ret_val.ShipDate = date.today().isoformat()
            ret_val.From = self._stamps_address(service, from_partner)
            ret_val.To = self._stamps_address(service, to_partner)
            ret_val.PackageType = self._stamps_package_type(package=package)
            ret_val.CubicPricing = self._stamps_package_is_cubic_pricing(package=package)
            ret_val.Length = l
            ret_val.Width = w
            ret_val.Height = h
            ret_val.ServiceType = self.stamps_service_type
            ret_val.WeightLb = weight
            ret_val.ContentType = self._stamps_content_type(package=package)
            ret.append((package.name + ret_val.ShipDate + str(ret_val.WeightLb) + self._stamps_hash_partner(to_partner), ret_val))
        if not ret and not package_carriers:
            weight = self._stamps_convert_weight(picking.shipping_weight)
            l, w, h = self._stamps_package_dimensions()

            ret_val = service.create_shipping()
            ret_val.ShipDate = date.today().isoformat()
            ret_val.From = self._stamps_address(service, from_partner)
            ret_val.To = self._stamps_address(service, to_partner)
            ret_val.PackageType = self._stamps_package_type()
            ret_val.CubicPricing = self._stamps_package_is_cubic_pricing()
            ret_val.Length = l
            ret_val.Width = w
            ret_val.Height = h
            ret_val.ServiceType = self.stamps_service_type
            ret_val.WeightLb = weight
            ret_val.ContentType = self._stamps_content_type()
            ret.append((picking.name + ret_val.ShipDate + str(ret_val.WeightLb) + self._stamps_hash_partner(to_partner), ret_val))

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
            'error_message': _('Error Retrieving Response from Stamps.com'),
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

    def _stamps_needs_customs(self, from_partner, to_partner, picking=None):
        return from_partner.country_id.code != to_partner.country_id.code or \
               (to_partner.country_id.code == 'US' and to_partner.state_id.code in STAMPS_US_APO_FPO_STATE_CODES)

    def stamps_send_shipping(self, pickings):
        res = []
        service = self._get_stamps_service()
        had_customs = False

        for picking in pickings:
            package_labels = []

            shippings = self._stamps_get_shippings_for_picking(service, picking)
            if not shippings:
                continue
            company, from_partner, to_partner = self._stamps_get_addresses_for_picking(picking)

            customs = None
            if self._stamps_needs_customs(from_partner, to_partner, picking=picking):
                customs = service.create_customs()
            had_customs = bool(had_customs or customs)

            try:
                for txn_id, shipping in shippings:
                    rates = service.get_rates(shipping)
                    if rates and len(rates) >= 1:
                        rate = rates[0]
                        shipping.Amount = rate.Amount
                        shipping.ServiceType = rate.ServiceType
                        shipping.DeliverDays = rate.DeliverDays
                        if hasattr(rate, 'DimWeighting'):
                            shipping.DimWeighting = rate.DimWeighting
                        shipping.RateCategory = rate.RateCategory
                        # shipping.ToState = rate.ToState
                        addons = []
                        if self.stamps_addon_sc:
                            add_on = service.create_add_on()
                            add_on.AddOnType = 'US-A-SC'
                            addons.append(add_on)
                        if self.stamps_addon_dc:
                            add_on = service.create_add_on()
                            add_on.AddOnType = 'US-A-DC'
                            addons.append(add_on)
                        if self.stamps_addon_hp:
                            add_on = service.create_add_on()
                            add_on.AddOnType = 'SC-A-HP'
                            addons.append(add_on)
                        shipping.AddOns.AddOnV17 = addons

                        extended_postage_info = service.create_extended_postage_info()
                        if self.is_amazon(picking=picking):
                            extended_postage_info.bridgeProfileType = 'Amazon MWS'

                        if customs:
                            customs.ContentType = shipping.ContentType
                            if not picking.package_ids:
                                raise ValidationError(_('Cannot use customs without packing items to ship first.'))
                            customs_total = 0.0
                            product_values = {}
                            # Note multiple packages will result in all product being on customs form.
                            # Recommended to ship one customs international package at a time.
                            for quant in picking.mapped('package_ids.quant_ids'):
                                # Customs should have the price for the destination but we may not be able
                                # to rely on the price from the SO (e.g. kit BoM)
                                product = quant.product_id
                                quantity = quant.quantity
                                price = product.lst_price
                                if to_partner.property_product_pricelist:
                                    # Note the quantity is used for the price, but it is per unit
                                    price = to_partner.property_product_pricelist.get_product_price(product, quantity, to_partner)
                                if product not in product_values:
                                    product_values[product] = {
                                        'quantity': 0.0,
                                        'value': 0.0,
                                    }
                                product_values[product]['quantity'] += quantity
                                product_values[product]['value'] += price * quantity
                            
                            # Note that Stamps will not allow you to use the scale weight if it is not equal
                            # to the sum of the customs lines.
                            # Thus we sum the line
                            new_total_weight = 0.0
                            customs_lines = []
                            for product, values in product_values.items():
                                customs_line = service.create_customs_lines()
                                customs_line.Description = product.name
                                customs_line.Quantity = values['quantity']
                                customs_total += round(values['value'], 2)
                                customs_line.Value = round(values['value'], 2)
                                line_weight = round(self._stamps_convert_weight(product.weight * values['quantity']), 2)
                                customs_line.WeightLb = line_weight
                                new_total_weight += line_weight
                                customs_line.HSTariffNumber = product.hs_code or ''
                                # customs_line.CountryOfOrigin =
                                customs_line.sku = product.default_code or ''
                                customs_lines.append(customs_line)
                            customs.CustomsLines.CustomsLine = customs_lines
                            shipping.DeclaredValue = round(customs_total, 2)
                            shipping.WeightLb = round(new_total_weight, 2)

                        label = service.get_label(shipping,
                                                  transaction_id=txn_id, image_type=self.stamps_image_type,
                                                  extended_postage_info=extended_postage_info,
                                                  customs=customs)
                        package_labels.append((txn_id, label))
            except WebFault as e:
                _logger.warning(e)
                if package_labels:
                    for name, label in package_labels:
                        body = _(u'Cancelling due to error: ', label.TrackingNumber)
                        try:
                            service.remove_label(label.TrackingNumber)
                        except WebFault as e:
                            raise ValidationError(e)
                        else:
                            picking.message_post(body=body)
                    raise ValidationError(_('Error on full shipment.  Attempted to cancel any previously shipped.'))
                raise ValidationError(_('Error on shipment. "%s"', e))
            else:
                carrier_price = 0.0
                tracking_numbers = []
                for name, label in package_labels:
                    body = _(u'Shipment created into Stamps.com <br/> <b>Tracking Number : <br/> "%s" </b>', label.TrackingNumber)
                    tracking_numbers.append(label.TrackingNumber)
                    carrier_price += float(label.Rate.Amount)
                    url = label.URL

                    url_spaces = url.split(' ')
                    attachments = []
                    for i, url in enumerate(url_spaces, 1):
                        response = urlopen(url)
                        attachment = response.read()
                        # Stamps.com sends labels that set the print rate (print speed) to 8 Inches per Second
                        # this is too fast for international/customs forms that have fine detail
                        # set it to the general minimum of 2IPS
                        if had_customs:
                            attachment = attachment.replace(b'^PR8,8,8\r\n', b'^PR2\r\n')
                        attachments.append(('LabelStamps-%s-%s.%s' % (label.TrackingNumber, i, self.stamps_image_type), attachment))
                    picking.message_post(body=body, attachments=attachments)
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
            all_tracking = picking.carrier_tracking_ref
            for tracking in all_tracking.split(','):
                service.remove_label(tracking.strip())
            picking.message_post(body=_(u'Shipment N° %s has been cancelled' % picking.carrier_tracking_ref))
            picking.write({'carrier_tracking_ref': '',
                           'carrier_price': 0.0})
        except WebFault as e:
            raise ValidationError(e)

    def stamps_rate_shipment_multi(self, order=None, picking=None, packages=None):
        if not packages:
            return self._stamps_rate_shipment_multi_package(order=order, picking=picking)
        else:
            rates = []
            for package in packages:
                rates += self._stamps_rate_shipment_multi_package(order=order, picking=picking, package=package)
            return rates

    def _stamps_rate_shipment_multi_package(self, order=None, picking=None, package=None):
        self.ensure_one()
        date_planned = fields.Datetime.now()
        if self.env.context.get('date_planned'):
            date_planned = self.env.context.get('date_planned')
        res = []
        service = self._get_stamps_service()
        shipping = self._get_stamps_shipping_multi(service, date_planned, order=order, picking=picking, package=package)
        rates = service.get_rates(shipping)
        for rate in rates:
            price = float(rate.Amount)
            if order:
                currency = order.currency_id
            else:
                currency = picking.sale_id.currency_id if picking.sale_id else picking.company_id.currency_id
            if currency.name != 'USD':
                quote_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                price = quote_currency.compute(rate.Amount, currency)

            delivery_days = rate.DeliverDays
            if delivery_days.find('-') >= 0:
                delivery_days = delivery_days.split('-')
                transit_days = int(delivery_days[-1])
            else:
                transit_days = int(delivery_days)
            date_delivered = None
            if transit_days > 0:
                date_delivered = self.calculate_date_delivered(date_planned, transit_days)
            service_code = rate.ServiceType
            carrier = self.stamps_find_delivery_carrier_for_service(service_code)
            if carrier:
                res.append({
                    'carrier': carrier,
                    'package': package or self.env['stock.quant.package'].browse(),
                    'success': True,
                    'price': price,
                    'error_message': False,
                    'warning_message': False,
                    'transit_days': transit_days,
                    'date_delivered': date_delivered,
                    'date_planned': date_planned,
                    'service_code': service_code,
                })
        if not res:
            res.append({
                'success': False,
                'price': 0.0,
                'error_message': _('No valid rates returned from Stamps.com'),
                'warning_message': False
            })
        return res

    def stamps_find_delivery_carrier_for_service(self, service_code):
        if self.stamps_service_type == service_code:
            return self
        # arbitrary decision, lets find the same user name
        carrier = self.search([('stamps_username', '=', self.stamps_username),
                               ('stamps_service_type', '=', service_code)
                               ], limit=1)
        return carrier
