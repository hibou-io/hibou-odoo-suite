# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import suds
from datetime import datetime
from copy import deepcopy
from odoo.addons.delivery_fedex.models import fedex_request

STATECODE_REQUIRED_COUNTRIES = fedex_request.STATECODE_REQUIRED_COUNTRIES


def sanitize_name(name):
    if isinstance(name, str):
        return name.replace('[', '').replace(']', '')
    return 'Unknown'


class FedexRequest(fedex_request.FedexRequest):
    _transit_days = {
        'ONE_DAYS': 1,
        'ONE_DAY': 1,
        'TWO_DAYS': 2,
        'THREE_DAYS': 3,
        'FOUR_DAYS': 4,
        'FIVE_DAYS': 5,
        'SIX_DAYS': 6,
        'SEVEN_DAYS': 7,
        'EIGHT_DAYS': 8,
        'NINE_DAYS': 9,
        'TEN_DAYS': 10,
    }

    _service_transit_days = {
        'FEDEX_2_DAY': 2,
        'FEDEX_2_DAY_AM': 2,
        'FEDEX_3_DAY_FREIGHT': 3,
        'FIRST_OVERNIGHT': 1,
        'PRIORITY_OVERNIGHT': 1,
        'STANDARD_OVERNIGHT': 1,
    }

    def set_recipient(self, recipient_partner, attn=None, residential=False):
        """
        Adds ATTN: and sanitizes against known 'illegal' common characters in names.
        :param recipient_partner: default
        :param attn: NEW add to contact name as an ' ATTN: $attn'
        :param residential: NEW allow ground home delivery
        :return:
        """
        Contact = self.client.factory.create('Contact')
        if recipient_partner.is_company:
            Contact.PersonName = ''
            Contact.CompanyName = sanitize_name(recipient_partner.name)
        else:
            Contact.PersonName = sanitize_name(recipient_partner.name)
            Contact.CompanyName = sanitize_name(recipient_partner.parent_id.name or '')

        if attn:
            Contact.PersonName = Contact.PersonName + ' ATTN: ' + str(attn)

        Contact.PhoneNumber = recipient_partner.phone or ''

        Address = self.client.factory.create('Address')
        Address.StreetLines = [recipient_partner.street or '', recipient_partner.street2 or '']
        Address.City = recipient_partner.city or ''
        if recipient_partner.country_id.code in STATECODE_REQUIRED_COUNTRIES:
            Address.StateOrProvinceCode = recipient_partner.state_id.code or ''
        else:
            Address.StateOrProvinceCode = ''
        Address.PostalCode = recipient_partner.zip or ''
        Address.CountryCode = recipient_partner.country_id.code or ''

        if residential:
            Address.Residential = True

        self.RequestedShipment.Recipient.Contact = Contact
        self.RequestedShipment.Recipient.Address = Address

    def add_package(self, weight_value, package_code=False, package_height=0, package_width=0, package_length=0, sequence_number=False, mode='shipping', ref=False, insurance=False, signature_required=False):
        # TODO remove in master and change the signature of a public method
        return self._add_package(weight_value=weight_value, package_code=package_code, package_height=package_height, package_width=package_width,
                                 package_length=package_length, sequence_number=sequence_number, mode=mode, po_number=False, dept_number=False, ref=ref, insurance=insurance, signature_required=signature_required)

    def _add_package(self, weight_value, package_code=False, package_height=0, package_width=0, package_length=0, sequence_number=False, mode='shipping', po_number=False, dept_number=False, ref=False, insurance=False, signature_required=False):
        package = self.client.factory.create('RequestedPackageLineItem')
        package_weight = self.client.factory.create('Weight')
        package_weight.Value = weight_value
        package_weight.Units = self.RequestedShipment.TotalWeight.Units

        if ref:
            customer_ref = self.client.factory.create('CustomerReference')
            customer_ref.CustomerReferenceType = 'CUSTOMER_REFERENCE'
            customer_ref.Value = str(ref)
            package.CustomerReferences.append(customer_ref)

        if insurance:
            insured = self.client.factory.create('Money')
            insured.Amount = insurance
            # TODO at some point someone might need currency here
            insured.Currency = 'USD'
            package.InsuredValue = insured

        special_service = self.client.factory.create("PackageSpecialServicesRequested")
        signature_detail = self.client.factory.create("SignatureOptionDetail")
        signature_detail.OptionType = 'DIRECT' if signature_required else 'NO_SIGNATURE_REQUIRED'
        special_service.SignatureOptionDetail = signature_detail
        package.SpecialServicesRequested = special_service

        package.PhysicalPackaging = 'BOX'
        if package_code == 'YOUR_PACKAGING':
            package.Dimensions.Height = package_height
            package.Dimensions.Width = package_width
            package.Dimensions.Length = package_length
            # TODO in master, add unit in product packaging and perform unit conversion
            package.Dimensions.Units = "IN" if self.RequestedShipment.TotalWeight.Units == 'LB' else 'CM'
        if po_number:
            po_reference = self.client.factory.create('CustomerReference')
            po_reference.CustomerReferenceType = 'P_O_NUMBER'
            po_reference.Value = po_number
            package.CustomerReferences.append(po_reference)
        if dept_number:
            dept_reference = self.client.factory.create('CustomerReference')
            dept_reference.CustomerReferenceType = 'DEPARTMENT_NUMBER'
            dept_reference.Value = dept_number
            package.CustomerReferences.append(dept_reference)

        package.Weight = package_weight
        if mode == 'rating':
            package.GroupPackageCount = 1
        if sequence_number:
            package.SequenceNumber = sequence_number
        else:
            self.hasOnePackage = True

        if mode == 'rating':
            self.RequestedShipment.RequestedPackageLineItems.append(package)
        else:
            self.RequestedShipment.RequestedPackageLineItems = package

    def shipping_charges_payment(self, shipping_charges_payment_account, third_party=False):
        """
        Allow 'shipping_charges_payment_account' to be considered 'third_party'
        :param shipping_charges_payment_account: default
        :param third_party: NEW add to indicate that the 'shipping_charges_payment_account' is third party.
        :return:
        """
        self.RequestedShipment.ShippingChargesPayment.PaymentType = 'SENDER' if not third_party else 'THIRD_PARTY'
        Payor = self.client.factory.create('Payor')
        Payor.ResponsibleParty.AccountNumber = shipping_charges_payment_account
        self.RequestedShipment.ShippingChargesPayment.Payor = Payor

    def shipment_request(self, dropoff_type, service_type, packaging_type, overall_weight_unit, saturday_delivery, ship_timestamp=None):
        self.RequestedShipment = self.client.factory.create('RequestedShipment')
        self.RequestedShipment.ShipTimestamp = ship_timestamp or datetime.now()
        self.RequestedShipment.DropoffType = dropoff_type
        self.RequestedShipment.ServiceType = service_type
        self.RequestedShipment.PackagingType = packaging_type
        # Resuest estimation of duties and taxes for international shipping
        if service_type in ['INTERNATIONAL_ECONOMY', 'INTERNATIONAL_PRIORITY']:
            self.RequestedShipment.EdtRequestType = 'ALL'
        else:
            self.RequestedShipment.EdtRequestType = 'NONE'
        self.RequestedShipment.PackageCount = 0
        self.RequestedShipment.TotalWeight.Units = overall_weight_unit
        self.RequestedShipment.TotalWeight.Value = 0
        self.listCommodities = []
        if saturday_delivery:
            timestamp_day = self.RequestedShipment.ShipTimestamp.strftime("%A")
            if (service_type == 'FEDEX_2_DAY' and timestamp_day == 'Thursday') or (service_type in ['PRIORITY_OVERNIGHT', 'FIRST_OVERNIGHT', 'INTERNATIONAL_PRIORITY'] and timestamp_day == 'Friday'):
                SpecialServiceTypes = self.client.factory.create('ShipmentSpecialServiceType')
                self.RequestedShipment.SpecialServicesRequested.SpecialServiceTypes = [SpecialServiceTypes.SATURDAY_DELIVERY]

    # Rating stuff

    def rate(self, date_planned=None, multi=False):
        """
        Response will contain 'transit_days' key with number of days.
        :param date_planned: Planned Outgoing shipment. Used to have FedEx tell us how long it will take for the package to arrive.
        :return:
        """
        if multi:
            multi_result = []
        if date_planned:
            self.RequestedShipment.ShipTimestamp = date_planned

        formatted_response = {'price': {}}
        del self.ClientDetail.Region
        if self.hasCommodities:
            self.RequestedShipment.CustomsClearanceDetail.Commodities = self.listCommodities

        try:
            self.response = self.client.service.getRates(WebAuthenticationDetail=self.WebAuthenticationDetail,
                                                         ClientDetail=self.ClientDetail,
                                                         TransactionDetail=self.TransactionDetail,
                                                         Version=self.VersionId,
                                                         RequestedShipment=self.RequestedShipment,
                                                         ReturnTransitAndCommit=True)  # New ReturnTransitAndCommit for CommitDetails in response

            if (self.response.HighestSeverity != 'ERROR' and self.response.HighestSeverity != 'FAILURE'):
                if not getattr(self.response, "RateReplyDetails", False):
                    raise Exception("No rating found")

                if not multi:
                    for rating in self.response.RateReplyDetails[0].RatedShipmentDetails:
                        formatted_response['price'][rating.ShipmentRateDetail.TotalNetFedExCharge.Currency] = rating.ShipmentRateDetail.TotalNetFedExCharge.Amount
                    if len(self.response.RateReplyDetails[0].RatedShipmentDetails) == 1:
                        if 'CurrencyExchangeRate' in self.response.RateReplyDetails[0].RatedShipmentDetails[0].ShipmentRateDetail:
                            formatted_response['price'][self.response.RateReplyDetails[0].RatedShipmentDetails[0].ShipmentRateDetail.CurrencyExchangeRate.FromCurrency] = self.response.RateReplyDetails[0].RatedShipmentDetails[0].ShipmentRateDetail.TotalNetFedExCharge.Amount / self.response.RateReplyDetails[0].RatedShipmentDetails[0].ShipmentRateDetail.CurrencyExchangeRate.Rate

                    # Hibou Delivery Planning
                    if hasattr(self.response.RateReplyDetails[0], 'DeliveryTimestamp') and self.response.RateReplyDetails[0].DeliveryTimestamp:
                        formatted_response['date_delivered'] = self.response.RateReplyDetails[0].DeliveryTimestamp
                        if hasattr(self.response.RateReplyDetails[0].CommitDetails[0], 'TransitTime'):
                            transit_days = self.response.RateReplyDetails[0].CommitDetails[0].TransitTime
                            transit_days = self._transit_days.get(transit_days, 0)
                            formatted_response['transit_days'] = transit_days
                    elif hasattr(self.response.RateReplyDetails[0], 'CommitDetails') and hasattr(self.response.RateReplyDetails[0].CommitDetails[0], 'CommitTimestamp'):
                        formatted_response['date_delivered'] = self.response.RateReplyDetails[0].CommitDetails[0].CommitTimestamp
                        formatted_response['transit_days'] = self._service_transit_days.get(self.response.RateReplyDetails[0].CommitDetails[0].ServiceType, 0)
                    elif hasattr(self.response.RateReplyDetails[0], 'CommitDetails') and hasattr(self.response.RateReplyDetails[0].CommitDetails[0], 'TransitTime'):
                        transit_days = self.response.RateReplyDetails[0].CommitDetails[0].TransitTime
                        transit_days = self._transit_days.get(transit_days, 0)
                        formatted_response['transit_days'] = transit_days
                else:
                    for rate_reply_detail in self.response.RateReplyDetails:
                        res = deepcopy(formatted_response)
                        res['service_code'] = rate_reply_detail.ServiceType
                        for rating in rate_reply_detail.RatedShipmentDetails:
                            res['price'][rating.ShipmentRateDetail.TotalNetFedExCharge.Currency] = rating.ShipmentRateDetail.TotalNetFedExCharge.Amount
                        if len(rate_reply_detail.RatedShipmentDetails) == 1:
                            if 'CurrencyExchangeRate' in rate_reply_detail.RatedShipmentDetails[0].ShipmentRateDetail:
                                res['price'][rate_reply_detail.RatedShipmentDetails[0].ShipmentRateDetail.CurrencyExchangeRate.FromCurrency] = rate_reply_detail.RatedShipmentDetails[0].ShipmentRateDetail.TotalNetFedExCharge.Amount / rate_reply_detail.RatedShipmentDetails[0].ShipmentRateDetail.CurrencyExchangeRate.Rate
                        # Hibou Delivery Planning
                        if hasattr(rate_reply_detail, 'DeliveryTimestamp') and rate_reply_detail.DeliveryTimestamp:
                            res['date_delivered'] = rate_reply_detail.DeliveryTimestamp
                            res['transit_days'] = self._service_transit_days.get(rate_reply_detail.ServiceType, 0)
                            if not res['transit_days'] and hasattr(rate_reply_detail.CommitDetails[0], 'TransitTime'):
                                transit_days = rate_reply_detail.CommitDetails[0].TransitTime
                                transit_days = self._transit_days.get(transit_days, 0)
                                res['transit_days'] = transit_days
                        elif hasattr(rate_reply_detail, 'CommitDetails') and hasattr(rate_reply_detail.CommitDetails[0], 'CommitTimestamp'):
                            res['date_delivered'] = rate_reply_detail.CommitDetails[0].CommitTimestamp
                            res['transit_days'] = self._service_transit_days.get(rate_reply_detail.ServiceType, 0)
                        elif hasattr(rate_reply_detail, 'CommitDetails') and hasattr(rate_reply_detail.CommitDetails[0], 'TransitTime'):
                            transit_days = rate_reply_detail.CommitDetails[0].TransitTime
                            transit_days = self._transit_days.get(transit_days, 0)
                            res['transit_days'] = transit_days
                        multi_result.append(res)

            else:
                errors_message = '\n'.join([("%s: %s" % (n.Code, n.Message)) for n in self.response.Notifications if (n.Severity == 'ERROR' or n.Severity == 'FAILURE')])
                formatted_response['errors_message'] = errors_message

            if any([n.Severity == 'WARNING' for n in self.response.Notifications]):
                warnings_message = '\n'.join([("%s: %s" % (n.Code, n.Message)) for n in self.response.Notifications if n.Severity == 'WARNING'])
                formatted_response['warnings_message'] = warnings_message

        except suds.WebFault as fault:
            formatted_response['errors_message'] = fault
        except IOError:
            formatted_response['errors_message'] = "Fedex Server Not Found"
        except Exception as e:
            formatted_response['errors_message'] = e.args[0]

        if multi:
            return multi_result
        return formatted_response
