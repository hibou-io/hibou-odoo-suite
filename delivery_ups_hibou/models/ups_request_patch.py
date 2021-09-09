from zeep.exceptions import Fault
from odoo.addons.delivery_ups.models.ups_request import UPSRequest
import logging
_logger = logging.getLogger(__name__)


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
    shipment.ShipmentRatingOptions.NegotiatedRatesIndicator = 1

    try:
        # Get rate using for provided detail
        response = client.service.ProcessRate(Request=request, CustomerClassification=classification, Shipment=shipment)

        # Check if ProcessRate is not success then return reason for that
        if response.Response.ResponseStatus.Code != "1":
            error_message = self.get_error_message(response.Response.ResponseStatus.Code, response.Response.ResponseStatus.Description)
            if multi:
                return [error_message]
            return error_message

        if not multi:
            rate = response.RatedShipment[0]
            charge = rate.TotalCharges

            # Some users are qualified to receive negotiated rates
            if 'NegotiatedRateCharges' in rate and rate.NegotiatedRateCharges and rate.NegotiatedRateCharges.TotalCharge.MonetaryValue:
                charge = rate.NegotiatedRateCharges.TotalCharge

            result = {
                'currency_code': charge.CurrencyCode,
                'price': charge.MonetaryValue,
            }

            # Hibou Delivery
            if hasattr(response.RatedShipment[0], 'GuaranteedDelivery') and hasattr(response.RatedShipment[0].GuaranteedDelivery, 'BusinessDaysInTransit'):
                result['transit_days'] = int(response.RatedShipment[0].GuaranteedDelivery.BusinessDaysInTransit)
            # End
        else:
            result = []
            for rate in response.RatedShipment:
                charge = rate.TotalCharges

                # Some users are qualified to receive negotiated rates
                if 'NegotiatedRateCharges' in rate and rate.NegotiatedRateCharges and rate.NegotiatedRateCharges.TotalCharge.MonetaryValue:
                    charge = rate.NegotiatedRateCharges.TotalCharge

                rated_shipment = {
                    'currency_code': charge.CurrencyCode,
                    'price': charge.MonetaryValue,
                }

                # Hibou Delivery
                if hasattr(response.RatedShipment[0], 'GuaranteedDelivery') and hasattr(
                        response.RatedShipment[0].GuaranteedDelivery, 'BusinessDaysInTransit'):
                    rated_shipment['transit_days'] = int(response.RatedShipment[0].GuaranteedDelivery.BusinessDaysInTransit)
                # End
                result.append(rated_shipment)
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


UPSRequest.get_shipping_price = patched_get_shipping_price
