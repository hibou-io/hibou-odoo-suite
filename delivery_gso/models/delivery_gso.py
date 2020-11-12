import pytz
from math import ceil
from requests import HTTPError
from hashlib import sha1

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

from .requests_gso import GSORequest

GSO_TZ = 'PST8PDT'


class ProductPackaging(models.Model):
    _inherit = 'product.packaging'

    package_carrier_type = fields.Selection(selection_add=[('gso', 'gso.com')])


class ProviderGSO(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('gso', 'gso.com')])
    gso_username = fields.Char(string='gso.com Username', groups='base.group_system')
    gso_password = fields.Char(string='gso.com Password', groups='base.group_system')
    gso_account_number = fields.Char(string='gso.com Account Number', groups='base.group_system')
    gso_default_packaging_id = fields.Many2one('product.packaging', string='Default Package Type')
    # For service type, SAM, SPM, and SEV require authorized accounts.
    gso_service_type = fields.Selection([('PDS', 'Priority Overnight'),
                                         ('EPS', 'Early Priority Overnight'),
                                         ('NPS', 'Noon Priority Overnight'),
                                         ('SDS', 'Saturday Delivery'),
                                         ('ESS', 'Early Saturday Delivery'),
                                         ('CPS', 'GSO Ground'),
                                         ('SAM', 'AM Select (8A-12P) Delivery Window'),
                                         ('SPM', 'PM Select (12P-4P) Delivery Window'),
                                         ('SEV', 'Evening Select (4P-8P) Delivery Window'),
                                         ],
                                        string="Service Type", default="CPS", help="Service Type determines speed of delivery")
    gso_image_type = fields.Selection([('NO_LABEL', 'No Label'),
                                       ('PAPER_LABEL', 'Paper Label'),
                                       ('ZPL_SHORT_LABEL', 'Short Label'),
                                       ('ZPL_LONG_LABEL', 'Long label'),
                                       ],
                                      string="Image Type", default="ZPL_SHORT_LABEL", help="Image Type is the type of Label to use")

    def _get_gso_service(self):
        return GSORequest(self.prod_environment,
                          self.gso_username,
                          self.gso_password,
                          self.gso_account_number)

    def _gso_make_ship_address(self, partner):
        # Addresses look like
        # {
        #   'ShipToCompany': '',
        #   'ShipToAttention': '',
        #   'ShipToPhone': '',
        #   'ShipToEmail': '',
        #   'DeliveryAddress1': '',
        #   'DeliveryAddress2': '',
        #   'DeliveryCity': '',
        #   'DeliveryState': '',
        #   'DeliveryZip': '',
        # }
        address = {}
        # ShipToCompany is required. ShipToAttention which is a person is not.
        if partner.name and not partner.parent_id:
            address['ShipToCompany'] = partner.name
        if partner.name and partner.parent_id:
            address['ShipToCompany'] = partner.parent_id.name  # or partner.parent_id.id.name ??
            address['ShipToAttention'] = partner.name

        if partner.phone:
            address['ShipToPhone'] = partner.phone
        if partner.email:
            address['ShipToEmail'] = partner.email
        if partner.street:
            address['DeliveryAddress1'] = partner.street
        if partner.street2:
            address['DeliveryAddress2'] = partner.street2
        if partner.city:
            address['DeliveryCity'] = partner.city
        if partner.state_id:
            address['DeliveryState'] = partner.state_id.code
        if partner.zip:
            address['DeliveryZip'] = partner.zip

        return address

    def _gso_make_shipper_address(self, warehouse, company):
        # Addresses look like
        # {
        #   'ShipperCompany': '',
        #   'ShipperContact': '',
        #   'ShipperPhone': '',
        #   'ShipperEmail': '',
        #   'PickupAddress1': '',
        #   'PickupAddress2': '',
        #   'PickupCity': '',
        #   'PickupState': '',
        #   'PickupZip': '',
        # }
        address = {}
        if company.name and not company.parent_id:
            address['ShipperCompany'] = company.name
        if company.name and company.parent_id:
            address['ShipperCompany'] = company.parent_id.name
            address['ShipperContact'] = company.name

        if warehouse.phone:
            address['ShipperPhone'] = warehouse.phone
        if warehouse.email:
            address['ShipperEmail'] = warehouse.email
        if warehouse.street:
            address['PickupAddress1'] = warehouse.street
        if warehouse.street2:
            address['PickupAddress2'] = warehouse.street2
        if warehouse.city:
            address['PickupCity'] = warehouse.city
        if warehouse.state_id:
            address['PickupState'] = warehouse.state_id.code
        if warehouse.zip:
            address['PickupZip'] = warehouse.zip

        return address

    def _gso_create_tracking_number(self, identifier):
        # Override for a more 'customized' tracking number
        # Expects a self.sudo()
        if not identifier:
            identifier = fields.Datetime.now()  # string in Odoo 11
        salt = self.env['ir.config_parameter'].sudo().get_param('database.secret')
        sha = sha1((identifier + salt).encode()).hexdigest()
        return sha[:20]

    def _gso_get_package_dimensions(self, package=None):
        if not package:
            package_type = self.gso_default_packaging_id
        else:
            package_type = package.packaging_id
        return {'Length': package_type.length, 'Width': package_type.width, 'Height': package_type.height}

    def _gso_convert_weight(self, weight_in_kg):
        # m(lb) = m(kg) / 0.45359237
        weight_in_lb = weight_in_kg / 0.45359237
        # If less than 8 oz...
        if weight_in_lb < 0.5:
            return 0
        else:
            # Round up to nearest lb
            return int(ceil(weight_in_lb))

    def gso_send_shipping(self, pickings):
        res = []
        sudoself = self.sudo()
        service = sudoself._get_gso_service()

        for picking in pickings:
            company = self.get_shipper_company(picking=picking)
            from_ = self.get_shipper_warehouse(picking=picking)
            to = self.get_recipient(picking=picking)
            address_type = 'B' if "company" in (to.company_type, to.parent_id.company_type) else 'R'

            request_body = {
                'AccountNumber': sudoself.gso_account_number,
                'Shipment': {
                    'ServiceCode': sudoself.gso_service_type,
                    'ShipmentLabelType': sudoself.gso_image_type,
                    'SignatureCode': 'SIG_NOT_REQD',
                    'DeliveryAddressType': address_type,
                    # 'ShipDate': fields.Date.today(),  # safer not to send in case you want to ship on a weekend
                },
            }
            request_body['Shipment'].update(self._gso_make_shipper_address(from_, company))
            request_body['Shipment'].update(self._gso_make_ship_address(to))

            # Automatic insurance at $100.0
            insurance_value = sudoself.get_insurance_value(picking=picking)
            if insurance_value:
                request_body['Shipment']['SignatureCode'] = 'SIG_REQD'
                if insurance_value > 100.0:
                    # Documentation says to set DeclaredValue ONLY if over $100.00
                    request_body['Shipment']['DeclaredValue'] = insurance_value

            cost = 0.0
            labels = {
                'thermal': [],
                'paper': [],
            }
            if picking.package_ids:
                # Every package will be a transaction
                for package in picking.package_ids:
                    request_body['Shipment']['Weight'] = self._gso_convert_weight(package.shipping_weight)
                    request_body['Shipment'].update(self._gso_get_package_dimensions(package))
                    request_body['Shipment']['ShipmentReference'] = package.name
                    request_body['Shipment']['TrackingNumber'] = self._gso_create_tracking_number(package.name)
                    try:
                        response = service.post_shipment(request_body)

                        if response.get('ThermalLabel'):
                            labels['thermal'].append((response['TrackingNumber'], response['ThermalLabel']))
                        elif response.get('PaperLabel'):
                            labels['paper'].append((response['TrackingNumber'], response['PaperLabel']))

                        if response.get('ShipmentCharges', {}).get('TotalCharge'):
                            cost += response['ShipmentCharges']['TotalCharge']
                    except HTTPError as e:
                        raise ValidationError(e)
            else:
                request_body['Shipment']['Weight'] = self._gso_convert_weight(picking.shipping_weight)
                request_body['Shipment'].update(self._gso_get_package_dimensions())
                request_body['Shipment']['ShipmentReference'] = picking.name
                request_body['Shipment']['TrackingNumber'] = self._gso_create_tracking_number(picking.name)
                try:
                    response = service.post_shipment(request_body)

                    if response.get('ThermalLabel'):
                        labels['thermal'].append((response['TrackingNumber'], response['ThermalLabel']))
                    elif response.get('PaperLabel'):
                        labels['paper'].append((response['TrackingNumber'], response['PaperLabel']))

                    if response.get('ShipmentCharges', {}).get('TotalCharge'):
                        cost += response['ShipmentCharges']['TotalCharge']
                except HTTPError as e:
                    raise ValidationError(e)

            # Handle results
            trackings = [l[0] for l in labels['thermal']] + [l(0) for l in labels['paper']]
            carrier_tracking_ref = ','.join(trackings)

            logmessage = _("Shipment created into GSO<br/>"
                           "<b>Tracking Numbers:</b> %s") % (carrier_tracking_ref, )
            attachments = []
            if labels['thermal']:
                attachments += [('LabelGSO-%s.zpl' % (l[0], ), l[1]) for l in labels['thermal']]
            if labels['paper']:
                attachments += [('LabelGSO-%s.pdf' % (l[0], ), l[1]) for l in labels['thermal']]
            picking.message_post(body=logmessage, attachments=attachments)
            shipping_data = {'exact_price': cost,
                             'tracking_number': carrier_tracking_ref}
            res.append(shipping_data)
        return res

    def gso_cancel_shipment(self, picking):
        sudoself = self.sudo()
        service = sudoself._get_gso_service()
        try:
            request_body = {
                'AccountNumber': sudoself.gso_account_number,
            }
            for tracking in picking.carrier_tracking_ref.split(','):
                request_body['TrackingNumber'] = tracking
                __ = service.delete_shipment(request_body)
        except HTTPError as e:
            raise ValidationError(e)
        picking.message_post(body=_('Shipment N° %s has been cancelled') % (picking.carrier_tracking_ref, ))
        picking.write({'carrier_tracking_ref': '', 'carrier_price': 0.0})

    def gso_rate_shipment(self, order):
        sudoself = self.sudo()
        service = sudoself._get_gso_service()
        from_ = sudoself.get_shipper_warehouse(order=order)
        to = sudoself.get_recipient(order=order)
        address_type = 'B' if "company" in (to.company_type, to.parent_id.company_type) else 'R'

        est_weight_value = self._gso_convert_weight(
            sum([(line.product_id.weight * line.product_uom_qty) for line in order.order_line]) or 0.0)

        date_planned = None
        if self.env.context.get('date_planned'):
            date_planned = self.env.context.get('date_planned')

        ship_date_utc = fields.Datetime.from_string(date_planned if date_planned else fields.Datetime.now())
        ship_date_utc = ship_date_utc.replace(tzinfo=pytz.utc)
        ship_date_gso = ship_date_utc.astimezone(pytz.timezone(GSO_TZ))
        ship_date_gso = fields.Datetime.to_string(ship_date_gso)

        request_body = {
            'AccountNumber': sudoself.gso_account_number,
            'OriginZip': from_.zip,
            'DestinationZip': to.zip,
            'ShipDate': ship_date_gso,
            'PackageDimension': self._gso_get_package_dimensions(),
            'PackageWeight': est_weight_value,
            'DeliveryAddressType': address_type,
        }

        result = service.get_rates_and_transit_time(request_body)

        delivery = list(filter(lambda d: d['ServiceCode'] == sudoself.gso_service_type, result['DeliveryServiceTypes']))
        if delivery:
            delivery = delivery[0]
            delivery_date_gso = delivery['DeliveryDate'].replace('T', ' ')
            delivery_date_gso = fields.Datetime.from_string(delivery_date_gso)
            delivery_date_gso = delivery_date_gso.replace(tzinfo=pytz.timezone(GSO_TZ))
            delivery_date_utc = delivery_date_gso.astimezone(pytz.utc)
            delivery_date_utc = fields.Datetime.to_string(delivery_date_utc)
            price = delivery.get('ShipmentCharges', {}).get('TotalCharge', 0.0)
            return {
                'success': True,
                'price': price,
                'error_message': False,
                'date_delivered': delivery_date_utc,
                'warning_message': _('TotalCharge not found.') if price == 0.0 else False,
            }

        raise Exception()
        return {
            'success': False,
            'price': 0.0,
            'error_message': _('Delivery Method not found in result'),
            'warning_message': False,
        }

    def gso_get_tracking_link(self, pickings):
        # No way to get a link specifically as their site only allows POST into tracking form.
        res = []
        for _ in pickings:
            res.append('https://www.gso.com/Tracking')
        return res
