# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.
import os
from zeep import Client, Plugin
from zeep.exceptions import Fault
from odoo.addons.delivery_ups.models.ups_request import UPSRequest, FixRequestNamespacePlug, LogPlugin, Package
import logging
_logger = logging.getLogger(__name__)

TNT_CODE_MAP = {
    'GND': '03',
    # TODO fill in the rest if needed....
}


def patched__init__(self, debug_logger, username, password, shipper_number, access_number, prod_environment):
    # patch to add the relative url for tnt_wsdl
    self.debug_logger = debug_logger
    # Product and Testing url
    self.endurl = "https://onlinetools.ups.com/webservices/"
    if not prod_environment:
        self.endurl = "https://wwwcie.ups.com/webservices/"

    # Basic detail require to authenticate
    self.username = username
    self.password = password
    self.shipper_number = shipper_number
    self.access_number = access_number

    self.rate_wsdl = '../api/RateWS.wsdl'
    self.ship_wsdl = '../api/Ship.wsdl'
    self.void_wsdl = '../api/Void.wsdl'
    self.tnt_wsdl = '../api/TNTWS.wsdl'
    self.ns = {'err': "http://www.ups.com/XMLSchema/XOLTWS/Error/v1.1"}


def patched_set_client(self, wsdl, api, root):
    # because of WSDL relative path we must patch
    wsdl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), wsdl)
    client = Client('file:///%s' % wsdl_path.lstrip('/'), plugins=[FixRequestNamespacePlug(root), LogPlugin(self.debug_logger)])
    self.factory_ns1 = client.type_factory('ns1')
    self.factory_ns2 = client.type_factory('ns2')
    self.factory_ns3 = client.type_factory('ns3')
    self._add_security_header(client, api)
    return client


def patched_get_shipping_price(self, shipment_info, packages, shipper, ship_from, ship_to, packaging_type, service_type,
                               saturday_delivery, cod_info, date_planned=False, multi=False):
    client = self._set_client(self.rate_wsdl, 'Rate', 'RateRequest')
    service = self._set_service(client, 'Rate')
    request = self.factory_ns3.RequestType()
    if multi:
        request.RequestOption = 'Shop'
    else:
        request.RequestOption = 'Rate'

    classification = self.factory_ns2.CodeDescriptionType()
    classification.Code = '00'  # Get rates for the shipper account
    classification.Description = 'Get rates for the shipper account'

    request_type = "rating"
    shipment = self.factory_ns2.ShipmentType()

    # Hibou Delivery
    if date_planned:
        if not isinstance(date_planned, str):
            date_planned = str(date_planned)
        shipment.DeliveryTimeInformation = self.factory_ns2.TimeInTransitRequestType()
        shipment.DeliveryTimeInformation.Pickup = self.factory_ns2.PickupType()
        shipment.DeliveryTimeInformation.Pickup.Date = date_planned.split(' ')[0]
    # End

    for package in self.set_package_detail(client, packages, packaging_type, ship_from, ship_to, cod_info, request_type):
        shipment.Package.append(package)

    shipment.Shipper = self.factory_ns2.ShipperType()
    shipment.Shipper.Name = shipper.name or ''
    shipment.Shipper.Address = self.factory_ns2.AddressType()
    shipment.Shipper.Address.AddressLine = [shipper.street or '', shipper.street2 or '']
    shipment.Shipper.Address.City = shipper.city or ''
    shipment.Shipper.Address.PostalCode = shipper.zip or ''
    shipment.Shipper.Address.CountryCode = shipper.country_id.code or ''
    if shipper.country_id.code in ('US', 'CA', 'IE'):
        shipment.Shipper.Address.StateProvinceCode = shipper.state_id.code or ''
    shipment.Shipper.ShipperNumber = self.shipper_number or ''
    # shipment.Shipper.Phone.Number = shipper.phone or ''

    shipment.ShipFrom = self.factory_ns2.ShipFromType()
    shipment.ShipFrom.Name = ship_from.name or ''
    shipment.ShipFrom.Address = self.factory_ns2.AddressType()
    shipment.ShipFrom.Address.AddressLine = [ship_from.street or '', ship_from.street2 or '']
    shipment.ShipFrom.Address.City = ship_from.city or ''
    shipment.ShipFrom.Address.PostalCode = ship_from.zip or ''
    shipment.ShipFrom.Address.CountryCode = ship_from.country_id.code or ''
    if ship_from.country_id.code in ('US', 'CA', 'IE'):
        shipment.ShipFrom.Address.StateProvinceCode = ship_from.state_id.code or ''
    # shipment.ShipFrom.Phone.Number = ship_from.phone or ''

    shipment.ShipTo = self.factory_ns2.ShipToType()
    shipment.ShipTo.Name = ship_to.name or ''
    shipment.ShipTo.Address = self.factory_ns2.AddressType()
    shipment.ShipTo.Address.AddressLine = [ship_to.street or '', ship_to.street2 or '']
    shipment.ShipTo.Address.City = ship_to.city or ''
    shipment.ShipTo.Address.PostalCode = ship_to.zip or ''
    shipment.ShipTo.Address.CountryCode = ship_to.country_id.code or ''
    if ship_to.country_id.code in ('US', 'CA', 'IE'):
        shipment.ShipTo.Address.StateProvinceCode = ship_to.state_id.code or ''
    # shipment.ShipTo.Phone.Number = ship_to.phone or ''
    if not ship_to.commercial_partner_id.is_company:
        shipment.ShipTo.Address.ResidentialAddressIndicator = None

    if not multi:
        shipment.Service = self.factory_ns2.CodeDescriptionType()
        shipment.Service.Code = service_type or ''
        shipment.Service.Description = 'Service Code'
        if service_type == "96":
            shipment.NumOfPieces = int(shipment_info.get('total_qty'))

    if saturday_delivery:
        shipment.ShipmentServiceOptions = self.factory_ns2.ShipmentServiceOptionsType()
        shipment.ShipmentServiceOptions.SaturdayDeliveryIndicator = saturday_delivery
    else:
        shipment.ShipmentServiceOptions = ''

    shipment.ShipmentRatingOptions = self.factory_ns2.ShipmentRatingOptionsType()
    shipment.ShipmentRatingOptions.NegotiatedRatesIndicator = '1'

    try:
        # Get rate using for provided detail
        response = client.service.ProcessRate(Request=request, CustomerClassification=classification, Shipment=shipment)

        # Check if ProcessRate is not success then return reason for that
        if response.Response.ResponseStatus.Code != "1":
            error_message = self.get_error_message(response.Response.ResponseStatus.Code, response.Response.ResponseStatus.Description)
            if multi:
                return [error_message]
            return error_message

        if multi:
            result = []
            tnt_response = None
            tnt_ready = False
            for rated_shipment in response.RatedShipment:
                res = {}
                res['service_code'] = rated_shipment.Service.Code
                res['currency_code'] = rated_shipment.TotalCharges.CurrencyCode
                negotiated_rate = 'NegotiatedRateCharges' in rated_shipment and rated_shipment.NegotiatedRateCharges.TotalCharge.MonetaryValue or None

                res['price'] = negotiated_rate or rated_shipment.TotalCharges.MonetaryValue
                # Hibou Delivery
                if hasattr(rated_shipment, 'GuaranteedDelivery') and hasattr(rated_shipment.GuaranteedDelivery, 'BusinessDaysInTransit'):
                    res['transit_days'] = int(rated_shipment.GuaranteedDelivery.BusinessDaysInTransit)

                if not res.get('transit_days') and date_planned:
                    if not tnt_response:
                        try:
                            tnt_client = self._set_client(self.tnt_wsdl, 'TimeInTransit', 'TimeInTransitRequest')
                            tnt_service = self._set_service(tnt_client, 'TimeInTransit')
                            tnt_request = self.factory_ns3.RequestType()
                            tnt_request.RequestOption = 'TNT'

                            tnt_ship_from = self.factory_ns2.RequestShipFromType()
                            tnt_ship_from.Address = self.factory_ns2.RequestShipFromAddressType()
                            tnt_ship_from.AttentionName = (ship_from.name or '')[:35]
                            tnt_ship_from.Name = (ship_from.parent_id.name or ship_from.name or '')[:35]
                            tnt_ship_from.Address.AddressLine = [l for l in [ship_from.street or '', ship_from.street2 or ''] if l]
                            tnt_ship_from.Address.City = ship_from.city or ''
                            tnt_ship_from.Address.PostalCode = ship_from.zip or ''
                            tnt_ship_from.Address.CountryCode = ship_from.country_id.code or ''
                            if ship_from.country_id.code in ('US', 'CA', 'IE'):
                                tnt_ship_from.Address.StateProvinceCode = ship_from.state_id.code or ''

                            tnt_ship_to = self.factory_ns2.RequestShipToType()
                            tnt_ship_to.Address = self.factory_ns2.RequestShipToAddressType()
                            tnt_ship_to.AttentionName = (ship_to.name or '')[:35]
                            tnt_ship_to.Name = (ship_to.parent_id.name or ship_to.name or '')[:35]
                            tnt_ship_to.Address.AddressLine = [l for l in [ship_to.street or '', ship_to.street2 or ''] if l]
                            tnt_ship_to.Address.City = ship_to.city or ''
                            tnt_ship_to.Address.PostalCode = ship_to.zip or ''
                            tnt_ship_to.Address.CountryCode = ship_to.country_id.code or ''
                            if ship_to.country_id.code in ('US', 'CA', 'IE'):
                                tnt_ship_to.Address.StateProvinceCode = ship_to.state_id.code or ''
                            if not ship_to.commercial_partner_id.is_company:
                                tnt_ship_to.Address.ResidentialAddressIndicator = None

                            tnt_pickup = self.factory_ns2.PickupType()
                            tnt_pickup.Date = date_planned.split(' ')[0].replace('-', '')
                            tnt_pickup.Time = date_planned.split(' ')[1].replace(':', '')

                            tnt_response = tnt_service.ProcessTimeInTransit(Request=tnt_request,
                                                                            ShipFrom=tnt_ship_from,
                                                                            ShipTo=tnt_ship_to,
                                                                            Pickup=tnt_pickup)
                            tnt_ready = tnt_response.Response.ResponseStatus.Code == "1"
                        except Exception as e:
                            _logger.warning('exception during the UPS Time In Transit request. ' + str(e))
                            _logger.exception(e)
                            tnt_ready = False
                            tnt_response = '-1'
                    if tnt_ready and hasattr(tnt_response, 'TransitResponse') and hasattr(tnt_response.TransitResponse, 'ServiceSummary'):
                        for service in tnt_response.TransitResponse.ServiceSummary:
                            if TNT_CODE_MAP.get(service.Service.Code) == res['service_code']:
                                if hasattr(service, 'EstimatedArrival') and hasattr(service.EstimatedArrival, 'BusinessDaysInTransit'):
                                    res['transit_days'] = int(service.EstimatedArrival.BusinessDaysInTransit)
                                    break
                result.append(res)
        else:
            result = {}
            result['currency_code'] = response.RatedShipment[0].TotalCharges.CurrencyCode

            # Some users are qualified to receive negotiated rates
            negotiated_rate = 'NegotiatedRateCharges' in response.RatedShipment[0] and response.RatedShipment[
                0].NegotiatedRateCharges.TotalCharge.MonetaryValue or None

            result['price'] = negotiated_rate or response.RatedShipment[0].TotalCharges.MonetaryValue
            # Hibou Delivery
            if hasattr(response.RatedShipment[0], 'GuaranteedDelivery') and hasattr(response.RatedShipment[0].GuaranteedDelivery, 'BusinessDaysInTransit'):
                result['transit_days'] = int(response.RatedShipment[0].GuaranteedDelivery.BusinessDaysInTransit)

            if not result.get('transit_days') and date_planned:
                # use TNT API to
                _logger.warning('   We would now use the TNT service. But who would show the transit days? 2')

        return result

    except Fault as e:
        code = e.detail.xpath("//err:PrimaryErrorCode/err:Code", namespaces=self.ns)[0].text
        description = e.detail.xpath("//err:PrimaryErrorCode/err:Description", namespaces=self.ns)[0].text
        error_message = self.get_error_message(code, description)
        if multi:
            return [error_message]
        return error_message
    except IOError as e:
        error_message = self.get_error_message('0', 'UPS Server Not Found:\n%s' % e)
        if multi:
            return [error_message]
        return error_message


def patched_send_shipping(self, shipment_info, packages, shipper, ship_from, ship_to, packaging_type, service_type, saturday_delivery, duty_payment, cod_info=None, label_file_type='GIF', ups_carrier_account=False):
    client = self._set_client(self.ship_wsdl, 'Ship', 'ShipmentRequest')
    request = self.factory_ns3.RequestType()
    request.RequestOption = 'nonvalidate'

    request_type = "shipping"
    label = self.factory_ns2.LabelSpecificationType()
    label.LabelImageFormat = self.factory_ns2.LabelImageFormatType()
    label.LabelImageFormat.Code = label_file_type
    label.LabelImageFormat.Description = label_file_type
    if label_file_type != 'GIF':
        label.LabelStockSize = self.factory_ns2.LabelStockSizeType()
        label.LabelStockSize.Height = '6'
        label.LabelStockSize.Width = '4'

    shipment = self.factory_ns2.ShipmentType()
    shipment.Description = shipment_info.get('description')

    for package in self.set_package_detail(client, packages, packaging_type, ship_from, ship_to, cod_info, request_type):
        shipment.Package.append(package)

    shipment.Shipper = self.factory_ns2.ShipperType()
    shipment.Shipper.Address = self.factory_ns2.ShipAddressType()
    shipment.Shipper.AttentionName = (shipper.name or '')[:35]
    shipment.Shipper.Name = (shipper.parent_id.name or shipper.name or '')[:35]
    shipment.Shipper.Address.AddressLine = [l for l in [shipper.street or '', shipper.street2 or ''] if l]
    shipment.Shipper.Address.City = shipper.city or ''
    shipment.Shipper.Address.PostalCode = shipper.zip or ''
    shipment.Shipper.Address.CountryCode = shipper.country_id.code or ''
    if shipper.country_id.code in ('US', 'CA', 'IE'):
        shipment.Shipper.Address.StateProvinceCode = shipper.state_id.code or ''
    shipment.Shipper.ShipperNumber = self.shipper_number or ''
    shipment.Shipper.Phone = self.factory_ns2.ShipPhoneType()
    shipment.Shipper.Phone.Number = self._clean_phone_number(shipper.phone)

    shipment.ShipFrom = self.factory_ns2.ShipFromType()
    shipment.ShipFrom.Address = self.factory_ns2.ShipAddressType()
    shipment.ShipFrom.AttentionName = (ship_from.name or '')[:35]
    shipment.ShipFrom.Name = (ship_from.parent_id.name or ship_from.name or '')[:35]
    shipment.ShipFrom.Address.AddressLine = [l for l in [ship_from.street or '', ship_from.street2 or ''] if l]
    shipment.ShipFrom.Address.City = ship_from.city or ''
    shipment.ShipFrom.Address.PostalCode = ship_from.zip or ''
    shipment.ShipFrom.Address.CountryCode = ship_from.country_id.code or ''
    if ship_from.country_id.code in ('US', 'CA', 'IE'):
        shipment.ShipFrom.Address.StateProvinceCode = ship_from.state_id.code or ''
    shipment.ShipFrom.Phone = self.factory_ns2.ShipPhoneType()
    shipment.ShipFrom.Phone.Number = self._clean_phone_number(ship_from.phone)

    shipment.ShipTo = self.factory_ns2.ShipToType()
    shipment.ShipTo.Address = self.factory_ns2.ShipToAddressType()
    shipment.ShipTo.AttentionName = (ship_to.name or '')[:35]
    shipment.ShipTo.Name = (ship_to.parent_id.name or ship_to.name or '')[:35]
    shipment.ShipTo.Address.AddressLine = [l for l in [ship_to.street or '', ship_to.street2 or ''] if l]
    shipment.ShipTo.Address.City = ship_to.city or ''
    shipment.ShipTo.Address.PostalCode = ship_to.zip or ''
    shipment.ShipTo.Address.CountryCode = ship_to.country_id.code or ''
    if ship_to.country_id.code in ('US', 'CA', 'IE'):
        shipment.ShipTo.Address.StateProvinceCode = ship_to.state_id.code or ''
    shipment.ShipTo.Phone = self.factory_ns2.ShipPhoneType()
    shipment.ShipTo.Phone.Number = self._clean_phone_number(shipment_info['phone'])
    if not ship_to.commercial_partner_id.is_company:
        shipment.ShipTo.Address.ResidentialAddressIndicator = None

    shipment.Service = self.factory_ns2.ServiceType()
    shipment.Service.Code = service_type or ''
    shipment.Service.Description = 'Service Code'
    if service_type == "96":
        shipment.NumOfPiecesInShipment = int(shipment_info.get('total_qty'))
    shipment.ShipmentRatingOptions = self.factory_ns2.RateInfoType()
    shipment.ShipmentRatingOptions.NegotiatedRatesIndicator = 1

    # Shipments from US to CA or PR require extra info
    if ship_from.country_id.code == 'US' and ship_to.country_id.code in ['CA', 'PR']:
        shipment.InvoiceLineTotal = self.factory_ns2.CurrencyMonetaryType()
        shipment.InvoiceLineTotal.CurrencyCode = shipment_info.get('itl_currency_code')
        shipment.InvoiceLineTotal.MonetaryValue = shipment_info.get('ilt_monetary_value')

    # set the default method for payment using shipper account
    payment_info = self.factory_ns2.PaymentInfoType()
    shipcharge = self.factory_ns2.ShipmentChargeType()
    shipcharge.Type = '01'

    # Bill Recevier 'Bill My Account'
    if ups_carrier_account:
        shipcharge.BillReceiver = self.factory_ns2.BillReceiverType()
        shipcharge.BillReceiver.Address = self.factory_ns2.BillReceiverAddressType()
        shipcharge.BillReceiver.AccountNumber = ups_carrier_account
        shipcharge.BillReceiver.Address.PostalCode = ship_to.zip
    else:
        shipcharge.BillShipper = self.factory_ns2.BillShipperType()
        shipcharge.BillShipper.AccountNumber = self.shipper_number or ''

    payment_info.ShipmentCharge = [shipcharge]

    if duty_payment == 'SENDER':
        duty_charge = self.factory_ns2.ShipmentChargeType()
        duty_charge.Type = '02'
        duty_charge.BillShipper = self.factory_ns2.BillShipperType()
        duty_charge.BillShipper.AccountNumber = self.shipper_number or ''
        payment_info.ShipmentCharge.append(duty_charge)

    shipment.PaymentInformation = payment_info

    if saturday_delivery:
        shipment.ShipmentServiceOptions = self.factory_ns2.ShipmentServiceOptionsType()
        shipment.ShipmentServiceOptions.SaturdayDeliveryIndicator = saturday_delivery
    else:
        shipment.ShipmentServiceOptions = ''
    self.shipment = shipment
    self.label = label
    self.request = request
    self.label_file_type = label_file_type


def patched_set_package_detail(self, client, packages, packaging_type, ship_from, ship_to, cod_info, request_type):
    Packages = []
    if request_type == "rating":
        MeasurementType = self.factory_ns2.CodeDescriptionType
    elif request_type == "shipping":
        MeasurementType = self.factory_ns2.ShipUnitOfMeasurementType
    for i, p in enumerate(packages):
        package = self.factory_ns2.PackageType()
        if hasattr(package, 'Packaging'):
            package.Packaging = self.factory_ns2.PackagingType()
            package.Packaging.Code = p.packaging_type or packaging_type or ''
        elif hasattr(package, 'PackagingType'):
            package.PackagingType = self.factory_ns2.CodeDescriptionType()
            package.PackagingType.Code = p.packaging_type or packaging_type or ''

        if p.dimension_unit and any(p.dimension.values()):
            package.Dimensions = self.factory_ns2.DimensionsType()
            package.Dimensions.UnitOfMeasurement = MeasurementType()
            package.Dimensions.UnitOfMeasurement.Code = p.dimension_unit or ''
            package.Dimensions.Length = p.dimension['length'] or ''
            package.Dimensions.Width = p.dimension['width'] or ''
            package.Dimensions.Height = p.dimension['height'] or ''

        if cod_info:
            package.PackageServiceOptions = self.factory_ns2.PackageServiceOptionsType()
            package.PackageServiceOptions.COD = self.factory_ns2.CODType()
            package.PackageServiceOptions.COD.CODFundsCode = str(cod_info['funds_code'])
            package.PackageServiceOptions.COD.CODAmount = self.factory_ns2.CODAmountType() if request_type == 'rating' else self.factory_ns2.CurrencyMonetaryType()
            package.PackageServiceOptions.COD.CODAmount.MonetaryValue = cod_info['monetary_value']
            package.PackageServiceOptions.COD.CODAmount.CurrencyCode = cod_info['currency']

        # Hibou Insurance & Signature Requirement
        if p.insurance_value:
            if not package.PackageServiceOptions:
                package.PackageServiceOptions = self.factory_ns2.PackageServiceOptionsType()
            if not package.PackageServiceOptions.DeclaredValue:
                if request_type == 'shipping':
                    package.PackageServiceOptions.DeclaredValue = self.factory_ns2.PackageDeclaredValueType()
                else:
                    package.PackageServiceOptions.DeclaredValue = self.factory_ns2.ShipperDeclaredValueType()
            package.PackageServiceOptions.DeclaredValue.MonetaryValue = p.insurance_value
            package.PackageServiceOptions.DeclaredValue.CurrencyCode = p.insurance_currency_code
        if p.signature_required:
            if not package.PackageServiceOptions:
                package.PackageServiceOptions = self.factory_ns2.PackageServiceOptionsType()
            if not package.PackageServiceOptions.DeliveryConfirmation:
                package.PackageServiceOptions.DeliveryConfirmation = self.factory_ns2.DeliveryConfirmationType()
            package.PackageServiceOptions.DeliveryConfirmation.DCISType = p.signature_required

        package.PackageWeight = self.factory_ns2.PackageWeightType()
        package.PackageWeight.UnitOfMeasurement = MeasurementType()
        package.PackageWeight.UnitOfMeasurement.Code = p.weight_unit or ''
        package.PackageWeight.Weight = p.weight or ''

        # Package and shipment reference text is only allowed for shipments within
        # the USA and within Puerto Rico. This is a UPS limitation.
        if (p.name and ship_from.country_id.code in ('US') and ship_to.country_id.code in ('US')):
            reference_number = self.factory_ns2.ReferenceNumberType()
            reference_number.Code = 'PM'
            reference_number.Value = p.name
            reference_number.BarCodeIndicator = p.name
            package.ReferenceNumber = reference_number

        Packages.append(package)
    return Packages


UPSRequest.__init__ = patched__init__
UPSRequest._set_client = patched_set_client
UPSRequest.get_shipping_price = patched_get_shipping_price
UPSRequest.send_shipping = patched_send_shipping
UPSRequest.set_package_detail = patched_set_package_detail


def patched__init__2(self, carrier, weight, quant_pack=False, name='',
                     insurance_value=False, insurance_currency_code=False, signature_required=False):
    self.weight = carrier._ups_convert_weight(weight, carrier.ups_package_weight_unit)
    self.weight_unit = carrier.ups_package_weight_unit
    self.name = name
    self.dimension_unit = carrier.ups_package_dimension_unit
    if quant_pack:
        self.dimension = {'length': quant_pack.packaging_length, 'width': quant_pack.width, 'height': quant_pack.height}
    else:
        self.dimension = {'length': carrier.ups_default_packaging_id.packaging_length, 'width': carrier.ups_default_packaging_id.width, 'height': carrier.ups_default_packaging_id.height}
    self.packaging_type = quant_pack and quant_pack.shipper_package_code or False
    self.insurance_value = insurance_value
    self.insurance_currency_code = insurance_currency_code
    self.signature_required = signature_required


Package.__init__ = patched__init__2
