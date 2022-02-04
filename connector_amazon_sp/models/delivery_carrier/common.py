# © 2021 Hibou Corp.

import zlib
from datetime import date, datetime
from base64 import b64decode

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class ProductPackaging(models.Model):
    _inherit = 'product.packaging'

    amazon_sp_mfn_allowed_services = fields.Text(
        string='Amazon SP MFN Allowed Methods',
        help='Comma separated list. e.g. "FEDEX_PTP_HOME_DELIVERY,FEDEX_PTP_SECOND_DAY,USPS_PTP_PRI_LFRB"')


class ProviderAmazonSP(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[
        # ('amazon_sp', 'Amazon Selling Partner'),  # TODO buy shipping for regular orders?
        ('amazon_sp_mfn', 'Amazon SP Merchant Fulfillment')
    ], ondelete={'amazon_sp_mfn': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0})})

    # Fields when uploading shipping to Amazon
    amazon_sp_carrier_code = fields.Char(string='Amazon Carrier Code',
                                         help='Specific carrier code, will default to "Other".')
    amazon_sp_carrier_name = fields.Char(string='Amazon Carrier Name',
                                         help='Specific carrier name, will default to regular name.')
    amazon_sp_shipping_method = fields.Char(string='Amazon Shipping Method',
                                            help='Specific shipping method, will default to "Standard"')
    # Fields when purchasing shipping from Amazon
    amazon_sp_mfn_allowed_services = fields.Text(
        string='Allowed Methods',
        help='Comma separated list. e.g. "FEDEX_PTP_HOME_DELIVERY,FEDEX_PTP_SECOND_DAY,USPS_PTP_PRI_LFRB"',
        default='FEDEX_PTP_HOME_DELIVERY,FEDEX_PTP_SECOND_DAY,USPS_PTP_PRI_LFRB')
    amazon_sp_mfn_label_formats = fields.Text(
        string='Allowed Label Formats',
        help='Comma separated list. e.g. "ZPL203,PNG"',
        default='ZPL203,PNG')

    def send_shipping(self, pickings):
        pickings = pickings.with_context(amz_pii_decrypt=1)
        self = self.with_context(amz_pii_decrypt=1)
        return super(ProviderAmazonSP, self).send_shipping(pickings)

    def is_amazon(self, order=None, picking=None):
        # Override from `delivery_hibou` to be used in stamps etc....
        if picking and picking.sale_id:
            so = picking.sale_id
            if so.amazon_bind_ids:
                return True
        if order and order.amazon_bind_ids:
            return True
        return super().is_amazon(order=order, picking=picking)

    def _amazon_sp_mfn_get_order_details(self, order):
        company = self.get_shipper_company(order=order)
        wh_partner = self.get_shipper_warehouse(order=order)

        if not order.amazon_bind_ids:
            raise ValidationError('Amazon shipping is not available for this order.')

        amazon_order_id = order.amazon_bind_ids[0].external_id
        from_ = dict(
            Name=company.name,
            AddressLine1=wh_partner.street,
            AddressLine2=wh_partner.street2 or '',
            City=wh_partner.city,
            StateOrProvinceCode=wh_partner.state_id.code,
            PostalCode=wh_partner.zip,
            CountryCode=wh_partner.country_id.code,
            Email=company.email or '',
            Phone=company.phone or '',
        )
        return amazon_order_id, from_

    def _amazon_sp_mfn_get_items_for_order(self, order):
        items = order.order_line.filtered(lambda l: l.amazon_bind_ids)
        return items.mapped(lambda l: (l.amazon_bind_ids[0].external_id, str(int(l.product_qty))))

    def _amazon_sp_mfn_get_items_for_package(self, package, order):
        items = []
        if not package.quant_ids:
            for move_line in package.current_picking_move_line_ids:
                line = order.order_line.filtered(lambda l: l.product_id.id == move_line.product_id.id and l.amazon_bind_ids)
                if line:
                    items.append((line[0].amazon_bind_ids[0].external_id, int(move_line.qty_done), {
                        'Unit': 'g',
                        'Value': line.product_id.weight * move_line.qty_done * 1000,
                    }, line.name))
        else:
            for quant in package.quant_ids:
                line = order.order_line.filtered(lambda l: l.product_id.id == quant.product_id.id and l.amazon_bind_ids)
                if line:
                    items.append((line[0].amazon_bind_ids[0].external_id, int(quant.quantity), {
                        'Unit': 'g',
                        'Value': line.product_id.weight * quant.quantity * 1000,
                    }, line.name))
        return items

    def _amazon_sp_mfn_convert_weight(self, weight):
        return int(weight * 1000), 'g'

    def _amazon_sp_mfn_pick_service(self, api_services, package=None):
        allowed_services = self.amazon_sp_mfn_allowed_services.split(',')
        if package and package.packaging_id.amazon_sp_mfn_allowed_services:
            allowed_services = package.packaging_id.amazon_sp_mfn_allowed_services.split(',')

        allowed_label_formats = self.amazon_sp_mfn_label_formats.split(',')
        services = []
        api_service_list = api_services['ShippingServiceList']
        if not isinstance(api_service_list, list):
            api_service_list = [api_service_list]
        for s in api_service_list:
            if s['ShippingServiceId'] in allowed_services:
                s_available_formats = s['AvailableLabelFormats']
                for l in allowed_label_formats:
                    if l in s_available_formats:
                        services.append({
                            'service_id': s['ShippingServiceId'],
                            'amount': float(s['Rate']['Amount']),
                            'label_format': l
                        })
                        break
        if services:
            return sorted(services, key=lambda s: s['amount'])[0]

        error = 'Cannot find applicable service. API Services: ' + \
                ','.join([s['ShippingServiceId'] for s in api_services['ShippingServiceList']]) + \
                ' Allowed Services: ' + self.amazon_sp_mfn_allowed_services
        raise ValidationError(error)

    def amazon_sp_mfn_send_shipping(self, pickings):
        res = []
        date_planned = datetime.now().replace(microsecond=0).isoformat()

        for picking in pickings:
            shipments = []

            picking_packages = picking.package_ids
            package_carriers = picking_packages.mapped('carrier_id')
            if package_carriers:
                # only ship ours
                picking_packages = picking_packages.filtered(lambda p: p.carrier_id == self and not p.carrier_tracking_ref)

            if not picking_packages:
                continue

            order = picking.sale_id.sudo()  # for having access to amazon bindings and backend

            # API comes from the binding backend
            if order.amazon_bind_ids:
                amazon_order = order.amazon_bind_ids[0]
                api_wrapped = amazon_order.backend_id.get_wrapped_api()
                # must_arrive_by_date not used, and `amazon_order.requested_date` can be False
                # so if it is to be used, we must decide what to do if there is no date.
                # must_arrive_by_date = fields.Datetime.from_string(amazon_order.requested_date).isoformat()
                api = api_wrapped.merchant_fulfillment()

            if not api:
                raise UserError('%s cannot be shipped by Amazon SP without a Sale Order or backend to use.' % picking)

            amazon_order_id, from_ = self._amazon_sp_mfn_get_order_details(order)
            for package in picking_packages:
                dimensions = {
                    'Length': package.packaging_id.length or 0.1,
                    'Width': package.packaging_id.width or 0.1,
                    'Height': package.packaging_id.height or 0.1,
                    'Unit': 'inches',
                }
                weight, weight_unit = self._amazon_sp_mfn_convert_weight(package.shipping_weight)
                items = self._amazon_sp_mfn_get_items_for_package(package, order)
                # Declared value
                inventory_value = self.get_inventory_value(picking=picking, package=package)
                sig_req = self.get_signature_required(picking=picking, package=package)

                ShipmentRequestDetails = {
                    'AmazonOrderId': amazon_order_id,
                    'ShipFromAddress': from_,
                    'Weight': {'Unit': weight_unit, 'Value': weight},
                    'SellerOrderId': order.name,
                    # The format of these dates cannot be determined, attempts:
                    # 2021-04-27 08:00:00
                    # 2021-04-27T08:00:00
                    # 2021-04-27T08:00:00Z
                    # 2021-04-27T08:00:00+00:00
                    # 'ShipDate': date_planned,
                    # 'MustArriveByDate': must_arrive_by_date,
                    'ShippingServiceOptions': {
                        'DeliveryExperience': 'DeliveryConfirmationWithSignature' if sig_req else 'NoTracking',
                        # CarrierWillPickUp is required
                        'CarrierWillPickUp': False,  # Note: Scheduled carrier pickup is available only using Dynamex (US), DPD (UK), and Royal Mail (UK).
                        'DeclaredValue': {
                            'Amount': inventory_value,
                            'CurrencyCode': 'USD'
                        },
                        # Conflicts at time of shipping for the above
                        # 'CarrierWillPickUpOption': 'NoPreference',
                        'LabelFormat': 'ZPL203'
                    },
                    'ItemList': [{
                        'OrderItemId': i[0],
                        'Quantity': i[1],
                        'ItemWeight': i[2],
                        'ItemDescription': i[3],
                    } for i in items],
                    'PackageDimensions': dimensions,
                }

                try:
                    # api_services = api.get_eligible_shipment_services(ShipmentRequestDetails, ShippingOfferingFilter={
                    #     'IncludePackingSlipWithLabel': False,
                    #     'IncludeComplexShippingOptions': False,
                    #     'CarrierWillPickUp': 'CarrierWillPickUp',
                    #     'DeliveryExperience': 'NoTracking',
                    # })
                    api_services = api.get_eligible_shipment_services(ShipmentRequestDetails)
                except api_wrapped.SellingApiForbiddenException:
                    raise UserError('Your Amazon SP API access does not include MerchantFulfillment')
                except api_wrapped.SellingApiException as e:
                    raise UserError('API Exception: ' + str(e.message))

                api_services = api_services.payload
                service = self._amazon_sp_mfn_pick_service(api_services, package=package)

                try:
                    shipment = api.create_shipment(ShipmentRequestDetails, service['service_id']).payload
                except api_wrapped.SellingApiForbiddenException:
                    raise UserError('Your Amazon SP API access does not include MerchantFulfillment')
                except api_wrapped.SellingApiException as e:
                    raise UserError('API Exception: ' + str(e.message))

                shipments.append((shipment, service))

            carrier_price = 0.0
            tracking_numbers =[]
            for shipment, service in shipments:
                tracking_number = shipment['TrackingId']
                carrier_name = shipment['ShippingService']['CarrierName']
                label_data = shipment['Label']['FileContents']['Contents']

                # So far, this is b64encoded and gzipped
                try:
                    label_decoded = b64decode(label_data)
                    try:
                        label_decoded = zlib.decompress(label_decoded)
                    except:
                        label_decoded = zlib.decompress(label_decoded, zlib.MAX_WBITS | 16)
                    label_data = label_decoded
                except:
                    # Oh well...
                    pass

                body = 'Shipment created into Amazon MFN<br/> <b>Tracking Number : <br/>' + tracking_number + '</b>'
                picking.message_post(body=body, attachments=[('Label%s-%s.%s' % (carrier_name, tracking_number, service['label_format']), label_data)])
                carrier_price += float(shipment['ShippingService']['Rate']['Amount'])
                tracking_numbers.append(tracking_number)
            shipping_data = {'exact_price': carrier_price, 'tracking_number': ','.join(tracking_numbers)}
            res = res + [shipping_data]

        return res

    def amazon_sp_mfn_rate_shipment_multi(self, order=None, picking=None, packages=None):
        if not packages:
            return self._amazon_sp_mfn_rate_shipment_multi_package(order=order, picking=picking)
        else:
            rates = []
            for package in packages:
                rates += self._amazon_sp_mfn_rate_shipment_multi_package(order=order, picking=picking, package=package)
            return rates

    def _amazon_sp_mfn_rate_shipment_multi_package(self, order=None, picking=None, package=None):
        res = []
        self.ensure_one()
        date_planned = fields.Datetime.now()
        if self.env.context.get('date_planned'):
            date_planned = self.env.context.get('date_planned')

        if order or not picking:
            raise UserError('Amazon SP MFN is intended to be used on imported orders.')
        if package:
            packages = package
        else:
            packages = picking.package_ids

        if not packages:
            raise UserError('Amazon SP MFN can only be used with packed items.')

        # to use current inventory in package
        packages = packages.with_context(picking_id=picking.id)

        order = picking.sale_id.sudo()
        api = None
        if order.amazon_bind_ids:
            amazon_order = order.amazon_bind_ids[0]
            api_wrapped = amazon_order.backend_id.get_wrapped_api()
            # must_arrive_by_date not used, and `amazon_order.requested_date` can be False
            # so if it is to be used, we must decide what to do if there is no date.
            # must_arrive_by_date = fields.Datetime.from_string(amazon_order.requested_date).isoformat()
            api = api_wrapped.merchant_fulfillment()

        if not api:
            raise UserError('%s cannot be shipped by Amazon SP without a Sale Order or backend to use.' % picking)

        amazon_order_id, from_ = self._amazon_sp_mfn_get_order_details(order)
        for package in packages:
            dimensions = {
                'Length': package.packaging_id.length or 0.1,
                'Width': package.packaging_id.width or 0.1,
                'Height': package.packaging_id.height or 0.1,
                'Unit': 'inches',
            }
            weight, weight_unit = self._amazon_sp_mfn_convert_weight(package.shipping_weight)
            items = self._amazon_sp_mfn_get_items_for_package(package, order)
            # Declared value
            inventory_value = self.get_insurance_value(picking=picking, package=package)
            sig_req = self.get_signature_required(picking=picking, package=packages)


            ShipmentRequestDetails = {
                'AmazonOrderId': amazon_order_id,
                'ShipFromAddress': from_,
                'Weight': {'Unit': weight_unit, 'Value': weight},
                'SellerOrderId': order.name,
                # The format of these dates cannot be determined, attempts:
                # 2021-04-27 08:00:00
                # 2021-04-27T08:00:00
                # 2021-04-27T08:00:00Z
                # 2021-04-27T08:00:00+00:00
                # 'ShipDate': date_planned,
                # 'MustArriveByDate': must_arrive_by_date,
                'ShippingServiceOptions': {
                    'DeliveryExperience': 'DeliveryConfirmationWithSignature' if sig_req else 'NoTracking',
                    # CarrierWillPickUp is required
                    'CarrierWillPickUp': False,
                    # Note: Scheduled carrier pickup is available only using Dynamex (US), DPD (UK), and Royal Mail (UK).
                    'DeclaredValue': {
                        'Amount': inventory_value,
                        'CurrencyCode': 'USD'
                    },
                    # Conflicts at time of shipping for the above
                    # 'CarrierWillPickUpOption': 'NoPreference',
                    'LabelFormat': 'ZPL203'
                },
                'ItemList': [{
                    'OrderItemId': i[0],
                    'Quantity': i[1],
                    'ItemWeight': i[2],
                    'ItemDescription': i[3],
                } for i in items],
                'PackageDimensions': dimensions,
            }

            try:
                # api_services = api.get_eligible_shipment_services(ShipmentRequestDetails, ShippingOfferingFilter={
                #     'IncludePackingSlipWithLabel': False,
                #     'IncludeComplexShippingOptions': False,
                #     'CarrierWillPickUp': 'CarrierWillPickUp',
                #     'DeliveryExperience': 'NoTracking',
                # })
                api_services = api.get_eligible_shipment_services(ShipmentRequestDetails)
            except api_wrapped.SellingApiForbiddenException:
                raise UserError('Your Amazon SP API access does not include MerchantFulfillment')
            except api_wrapped.SellingApiException as e:
                raise UserError('API Exception: ' + str(e.message))

            api_services = api_services.payload
            # project into distinct carrier
            allowed_services = self.amazon_sp_mfn_allowed_services.split(',')
            if package and package.packaging_id.amazon_sp_mfn_allowed_services:
                allowed_services = package.packaging_id.amazon_sp_mfn_allowed_services.split(',')

            api_service_list = api_services['ShippingServiceList']
            if not isinstance(api_service_list, list):
                api_service_list = [api_service_list]

            for s in filter(lambda s: s['ShippingServiceId'] in allowed_services, api_service_list):
                _logger.warning('ShippingService: ' + str(s))
                service_code = s['ShippingServiceId']
                carrier = self.amazon_sp_mfn_find_delivery_carrier_for_service(service_code)
                if carrier:
                    res.append({
                        'carrier': carrier,
                        'package': package or self.env['stock.quant.package'].browse(),
                        'success': True,
                        'price': s['Rate']['Amount'],
                        'error_message': False,
                        'warning_message': False,
                        # 'transit_days': transit_days,
                        'date_delivered': s['LatestEstimatedDeliveryDate'] if s['LatestEstimatedDeliveryDate'] else s['EarliestEstimatedDeliveryDate'],
                        'date_planned': date_planned,
                        'service_code': service_code,
                    })
            if not res:
                res.append({
                    'success': False,
                    'price': 0.0,
                    'error_message': 'No valid rates returned from AmazonSP-MFN',
                    'warning_message': False
                })
            return res

    def amazon_sp_mfn_find_delivery_carrier_for_service(self, service_code):
        if self.amazon_sp_mfn_allowed_services == service_code:
            return self
        carrier = self.search([('amazon_sp_mfn_allowed_services', '=', service_code),
                               ('delivery_type', '=', 'amazon_sp_mfn')
                               ], limit=1)
        return carrier
