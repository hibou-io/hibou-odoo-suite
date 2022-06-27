# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from os import path as os_path
import suds
from odoo.addons.delivery_ups.models.ups_request import UPSRequest, Package

SUDS_VERSION = suds.__version__

import logging
_logger = logging.getLogger(__name__)

# If you're getting SOAP/suds errors
# logging.getLogger('suds.client').setLevel(logging.DEBUG)

TNT_CODE_MAP = {
    'GND': '03',
    # TODO fill in the rest if needed....
}


def patched__init__(self, debug_logger, username, password, shipper_number, access_number, prod_environment):
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
    dirname = os_path.dirname(__file__)
    self.tnt_wsdl = os_path.join(dirname, '../api/TNTWS.wsdl')


def patched_get_shipping_price(self, shipment_info, packages, shipper, ship_from, ship_to, packaging_type, service_type,
                               saturday_delivery, cod_info, date_planned=False, multi=False):
    client = self._set_client(self.rate_wsdl, 'Rate', 'RateRequest')

    request = client.factory.create('ns0:RequestType')

    request.RequestOption = 'Rate'
    if multi:
        request.RequestOption = 'Shop'

    classification = client.factory.create('ns2:CodeDescriptionType')
    classification.Code = '00'  # Get rates for the shipper account
    classification.Description = 'Get rates for the shipper account'

    namespace = 'ns2'
    shipment = client.factory.create('{}:ShipmentType'.format(namespace))

    # Hibou Delivery
    if date_planned:
        if not isinstance(date_planned, str):
            date_planned = str(date_planned)
        shipment.DeliveryTimeInformation = client.factory.create('{}:TimeInTransitRequestType'.format(namespace))
        shipment.DeliveryTimeInformation.Pickup = client.factory.create('{}:PickupType'.format(namespace))
        shipment.DeliveryTimeInformation.Pickup.Date = date_planned.split(' ')[0]
    # End

    for package in self.set_package_detail(client, packages, packaging_type, namespace, ship_from, ship_to, cod_info):
        shipment.Package.append(package)

    shipment.Shipper.Name = shipper.name or ''
    shipment.Shipper.Address.AddressLine = [shipper.street or '', shipper.street2 or '']
    shipment.Shipper.Address.City = shipper.city or ''
    shipment.Shipper.Address.PostalCode = shipper.zip or ''
    shipment.Shipper.Address.CountryCode = shipper.country_id.code or ''
    if shipper.country_id.code in ('US', 'CA', 'IE'):
        shipment.Shipper.Address.StateProvinceCode = shipper.state_id.code or ''
    shipment.Shipper.ShipperNumber = self.shipper_number or ''
    # shipment.Shipper.Phone.Number = shipper.phone or ''

    shipment.ShipFrom.Name = ship_from.name or ''
    shipment.ShipFrom.Address.AddressLine = [ship_from.street or '', ship_from.street2 or '']
    shipment.ShipFrom.Address.City = ship_from.city or ''
    shipment.ShipFrom.Address.PostalCode = ship_from.zip or ''
    shipment.ShipFrom.Address.CountryCode = ship_from.country_id.code or ''
    if ship_from.country_id.code in ('US', 'CA', 'IE'):
        shipment.ShipFrom.Address.StateProvinceCode = ship_from.state_id.code or ''
    # shipment.ShipFrom.Phone.Number = ship_from.phone or ''

    shipment.ShipTo.Name = ship_to.name or ''
    shipment.ShipTo.Address.AddressLine = [ship_to.street or '', ship_to.street2 or '']
    shipment.ShipTo.Address.City = ship_to.city or ''
    shipment.ShipTo.Address.PostalCode = ship_to.zip or ''
    shipment.ShipTo.Address.CountryCode = ship_to.country_id.code or ''
    if ship_to.country_id.code in ('US', 'CA', 'IE'):
        shipment.ShipTo.Address.StateProvinceCode = ship_to.state_id.code or ''
    # shipment.ShipTo.Phone.Number = ship_to.phone or ''
    if not ship_to.commercial_partner_id.is_company:
        shipment.ShipTo.Address.ResidentialAddressIndicator = suds.null()

    shipment.Service.Code = service_type or ''
    shipment.Service.Description = 'Service Code'
    if service_type == "96":
        shipment.NumOfPieces = int(shipment_info.get('total_qty'))

    if saturday_delivery:
        shipment.ShipmentServiceOptions.SaturdayDeliveryIndicator = saturday_delivery
    else:
        shipment.ShipmentServiceOptions = ''

    shipment.ShipmentRatingOptions.NegotiatedRatesIndicator = '1'

    try:
        # Get rate using for provided detail
        response = client.service.ProcessRate(Request=request, CustomerClassification=classification, Shipment=shipment)

        # Check if ProcessRate is not success then return reason for that
        if response.Response.ResponseStatus.Code != "1":
            return self.get_error_message(response.Response.ResponseStatus.Code,
                                          response.Response.ResponseStatus.Description)

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
                            tnt_request = tnt_client.factory.create('tnt:TimeInTransitRequest')
                            tnt_request.Request.RequestOption = 'TNT'

                            tnt_request.ShipFrom.Address.City = ship_from.city or ''
                            tnt_request.ShipFrom.Address.CountryCode = ship_from.country_id.code or ''
                            tnt_request.ShipFrom.Address.PostalCode = ship_from.zip or ''
                            if ship_from.country_id.code in ('US', 'CA', 'IE'):
                                tnt_request.ShipFrom.Address.StateProvinceCode = ship_from.state_id.code or ''

                            tnt_request.ShipTo.Address.City = ship_to.city or ''
                            tnt_request.ShipTo.Address.CountryCode = ship_to.country_id.code or ''
                            tnt_request.ShipTo.Address.PostalCode = ship_to.zip or ''
                            if ship_to.country_id.code in ('US', 'CA', 'IE'):
                                tnt_request.ShipTo.Address.StateProvinceCode = ship_to.state_id.code or ''

                            tnt_request.Pickup.Date = date_planned.split(' ')[0].replace('-', '')
                            tnt_request.Pickup.Time = date_planned.split(' ')[1].replace(':', '')

                            # tnt_request_transit_from = tnt_client.factory.create('ns1:TransitFrom')
                            tnt_response = tnt_client.service.ProcessTimeInTransit(Request=tnt_request.Request,
                                                                                   ShipFrom=tnt_request.ShipFrom,
                                                                                   ShipTo=tnt_request.ShipTo,
                                                                                   Pickup=tnt_request.Pickup)
                            tnt_ready = tnt_response.Response.ResponseStatus.Code == "1"
                        except Exception as e:
                            _logger.warning('exception during the UPS Time In Transit request. ' + str(e))
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

        # End

        return result

    except suds.WebFault as e:
        # childAtPath behaviour is changing at version 0.6
        prefix = ''
        if SUDS_VERSION >= "0.6":
            prefix = '/Envelope/Body/Fault'
        return self.get_error_message(
            e.document.childAtPath(prefix + '/detail/Errors/ErrorDetail/PrimaryErrorCode/Code').getText(),
            e.document.childAtPath(prefix + '/detail/Errors/ErrorDetail/PrimaryErrorCode/Description').getText())
    except IOError as e:
        return self.get_error_message('0', 'UPS Server Not Found:\n%s' % e)


def patched_send_shipping(self, shipment_info, packages, shipper, ship_from, ship_to, packaging_type, service_type, saturday_delivery, cod_info=None, label_file_type='GIF', ups_carrier_account=False):
    client = self._set_client(self.ship_wsdl, 'Ship', 'ShipmentRequest')

    request = client.factory.create('ns0:RequestType')
    request.RequestOption = 'nonvalidate'

    namespace = 'ns3'
    label = client.factory.create('{}:LabelSpecificationType'.format(namespace))

    label.LabelImageFormat.Code = label_file_type
    label.LabelImageFormat.Description = label_file_type
    if label_file_type != 'GIF':
        label.LabelStockSize.Height = '6'
        label.LabelStockSize.Width = '4'

    shipment = client.factory.create('{}:ShipmentType'.format(namespace))
    shipment.Description = shipment_info.get('description')

    for package in self.set_package_detail(client, packages, packaging_type, namespace, ship_from, ship_to, cod_info):
        shipment.Package.append(package)

    shipment.Shipper.AttentionName = shipper.name or ''
    shipment.Shipper.Name = shipper.parent_id.name or shipper.name or ''
    shipment.Shipper.Address.AddressLine = [l for l in [shipper.street or '', shipper.street2 or ''] if l]
    shipment.Shipper.Address.City = shipper.city or ''
    shipment.Shipper.Address.PostalCode = shipper.zip or ''
    shipment.Shipper.Address.CountryCode = shipper.country_id.code or ''
    if shipper.country_id.code in ('US', 'CA', 'IE'):
        shipment.Shipper.Address.StateProvinceCode = shipper.state_id.code or ''
    shipment.Shipper.ShipperNumber = self.shipper_number or ''
    shipment.Shipper.Phone.Number = self._clean_phone_number(shipper.phone)

    shipment.ShipFrom.AttentionName = ship_from.name or ''
    shipment.ShipFrom.Name = ship_from.parent_id.name or ship_from.name or ''
    shipment.ShipFrom.Address.AddressLine = [l for l in [ship_from.street or '', ship_from.street2 or ''] if l]
    shipment.ShipFrom.Address.City = ship_from.city or ''
    shipment.ShipFrom.Address.PostalCode = ship_from.zip or ''
    shipment.ShipFrom.Address.CountryCode = ship_from.country_id.code or ''
    if ship_from.country_id.code in ('US', 'CA', 'IE'):
        shipment.ShipFrom.Address.StateProvinceCode = ship_from.state_id.code or ''
    shipment.ShipFrom.Phone.Number = self._clean_phone_number(ship_from.phone)

    shipment.ShipTo.AttentionName = ship_to.name or ''
    shipment.ShipTo.Name = ship_to.parent_id.name or ship_to.name or ''
    shipment.ShipTo.Address.AddressLine = [l for l in [ship_to.street or '', ship_to.street2 or ''] if l]
    shipment.ShipTo.Address.City = ship_to.city or ''
    shipment.ShipTo.Address.PostalCode = ship_to.zip or ''
    shipment.ShipTo.Address.CountryCode = ship_to.country_id.code or ''
    if ship_to.country_id.code in ('US', 'CA', 'IE'):
        shipment.ShipTo.Address.StateProvinceCode = ship_to.state_id.code or ''
    shipment.ShipTo.Phone.Number = self._clean_phone_number(shipment_info['phone'])
    if not ship_to.commercial_partner_id.is_company:
        shipment.ShipTo.Address.ResidentialAddressIndicator = suds.null()

    shipment.Service.Code = service_type or ''
    shipment.Service.Description = 'Service Code'
    if service_type == "96":
        shipment.NumOfPiecesInShipment = int(shipment_info.get('total_qty'))
    shipment.ShipmentRatingOptions.NegotiatedRatesIndicator = 1

    # Shipments from US to CA or PR require extra info
    if ship_from.country_id.code == 'US' and ship_to.country_id.code in ['CA', 'PR']:
        shipment.InvoiceLineTotal.CurrencyCode = shipment_info.get('itl_currency_code')
        shipment.InvoiceLineTotal.MonetaryValue = shipment_info.get('ilt_monetary_value')

    # set the default method for payment using shipper account
    payment_info = client.factory.create('ns3:PaymentInformation')
    shipcharge = client.factory.create('ns3:ShipmentCharge')
    shipcharge.Type = '01'

    # Bill Recevier 'Bill My Account'
    if ups_carrier_account:
        shipcharge.BillReceiver.AccountNumber = ups_carrier_account
        shipcharge.BillReceiver.Address.PostalCode = ship_to.zip
    else:
        shipcharge.BillShipper.AccountNumber = self.shipper_number or ''

    payment_info.ShipmentCharge = shipcharge
    shipment.PaymentInformation = payment_info

    if saturday_delivery:
        shipment.ShipmentServiceOptions.SaturdayDeliveryIndicator = saturday_delivery
    else:
        shipment.ShipmentServiceOptions = ''

    try:
        response = client.service.ProcessShipment(
            Request=request, Shipment=shipment,
            LabelSpecification=label)

        # Check if shipment is not success then return reason for that
        if response.Response.ResponseStatus.Code != "1":
            return self.get_error_message(response.Response.ResponseStatus.Code, response.Response.ResponseStatus.Description)

        result = {}
        result['label_binary_data'] = {}
        for package in response.ShipmentResults.PackageResults:
            result['label_binary_data'][package.TrackingNumber] = self.save_label(package.ShippingLabel.GraphicImage, label_file_type=label_file_type)
        result['tracking_ref'] = response.ShipmentResults.ShipmentIdentificationNumber
        result['currency_code'] = response.ShipmentResults.ShipmentCharges.TotalCharges.CurrencyCode

        # Some users are qualified to receive negotiated rates
        negotiated_rate = 'NegotiatedRateCharges' in response.ShipmentResults and response.ShipmentResults.NegotiatedRateCharges.TotalCharge.MonetaryValue or None

        result['price'] = negotiated_rate or response.ShipmentResults.ShipmentCharges.TotalCharges.MonetaryValue
        return result

    except suds.WebFault as e:
        # childAtPath behaviour is changing at version 0.6
        prefix = ''
        if SUDS_VERSION >= "0.6":
            prefix = '/Envelope/Body/Fault'
        return self.get_error_message(e.document.childAtPath(prefix + '/detail/Errors/ErrorDetail/PrimaryErrorCode/Code').getText(),
                                      e.document.childAtPath(prefix + '/detail/Errors/ErrorDetail/PrimaryErrorCode/Description').getText())
    except IOError as e:
        return self.get_error_message('0', 'UPS Server Not Found:\n%s' % e)


def patched_set_package_detail(self, client, packages, packaging_type, namespace, ship_from, ship_to, cod_info):
    Packages = []
    for i, p in enumerate(packages):
        package = client.factory.create('{}:PackageType'.format(namespace))
        if hasattr(package, 'Packaging'):
            package.Packaging.Code = p.packaging_type or packaging_type or ''
        elif hasattr(package, 'PackagingType'):
            package.PackagingType.Code = p.packaging_type or packaging_type or ''

        # Hibou Insurance & Signature Requirement
        if p.insurance_value:
            package.PackageServiceOptions.DeclaredValue.MonetaryValue = p.insurance_value
            package.PackageServiceOptions.DeclaredValue.CurrencyCode = p.insurance_currency_code
        if p.signature_required:
            package.PackageServiceOptions.DeliveryConfirmation.DCISType = p.signature_required

        if p.dimension_unit and any(p.dimension.values()):
            package.Dimensions.UnitOfMeasurement.Code = p.dimension_unit or ''
            package.Dimensions.Length = p.dimension['length'] or ''
            package.Dimensions.Width = p.dimension['width'] or ''
            package.Dimensions.Height = p.dimension['height'] or ''

        if cod_info:
            package.PackageServiceOptions.COD.CODFundsCode = str(cod_info['funds_code'])
            package.PackageServiceOptions.COD.CODAmount.MonetaryValue = cod_info['monetary_value']
            package.PackageServiceOptions.COD.CODAmount.CurrencyCode = cod_info['currency']

        package.PackageWeight.UnitOfMeasurement.Code = p.weight_unit or ''
        package.PackageWeight.Weight = p.weight or ''

        # Package and shipment reference text is only allowed for shipments within
        # the USA and within Puerto Rico. This is a UPS limitation.
        if (p.name and ship_from.country_id.code in ('US') and ship_to.country_id.code in ('US')):
            reference_number = client.factory.create('ns3:ReferenceNumberType')
            reference_number.Code = 'PM'
            reference_number.Value = p.name
            reference_number.BarCodeIndicator = p.name
            package.ReferenceNumber = reference_number

        Packages.append(package)
    return Packages


UPSRequest.__init__ = patched__init__
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
        self.dimension = {'length': quant_pack.length, 'width': quant_pack.width, 'height': quant_pack.height}
    else:
        self.dimension = {'length': carrier.ups_default_packaging_id.length, 'width': carrier.ups_default_packaging_id.width, 'height': carrier.ups_default_packaging_id.height}
    self.packaging_type = quant_pack and quant_pack.shipper_package_code or False
    self.insurance_value = insurance_value
    self.insurance_currency_code = insurance_currency_code
    self.signature_required = signature_required


Package.__init__ = patched__init__2
