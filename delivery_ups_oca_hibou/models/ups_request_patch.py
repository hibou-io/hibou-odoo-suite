# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo.addons.delivery_ups_oca.models.ups_request import UpsRequest

import logging

_logger = logging.getLogger(__name__)



def _quant_package_data(self, package, picking):
    # TODO do we want to call this without a package?
    if not package and picking.package_ids:
        package = picking.package_ids
    currency = picking.sale_id.currency_id if picking.sale_id else picking.company_id.currency_id
    insurance_currency_code = currency.name
    res = []
    NumOfPieces = picking.number_of_packages
    PackageWeight = picking.shipping_weight
    if package:
        NumOfPieces = len(package)
        # PackageWeight = sum(package.mapped('shipping_weight'))
        for p in package:
            package_data = {
                "Description": p.name,
                "NumOfPieces": str(NumOfPieces),
                "Packaging": {
                    "Code": p.package_type_id.shipper_package_code,
                    "Description": p.name,
                },
                "Dimensions": {
                    "UnitOfMeasurement": {"Code": self.package_dimension_code},
                    "Length": str(p.package_type_id.packaging_length),
                    "Width": str(p.package_type_id.width),
                    "Height": str(p.package_type_id.height),
                },
                "PackageWeight": {
                    "UnitOfMeasurement": {"Code": self.package_weight_code},
                    "Weight": str(p.shipping_weight),
                },
                "PackageServiceOptions": "",
            }
            # Hibou Insurance & Signature Requirement
            insurance_value = self.carrier.get_insurance_value(picking=picking, package=p)
            if insurance_value:
                if not package_data['PackageServiceOptions']:
                    package_data['PackageServiceOptions'] = {}
                package_data['PackageServiceOptions']['DeclaredValue'] = {
                    'Type': {'Code': '01'},
                    'MonetaryValue': str(insurance_value),
                    'CurrencyCode': insurance_currency_code,
                }
            signature_required = self.carrier._get_ups_signature_required(picking=picking, package=p)
            if signature_required:
                if not package_data['PackageServiceOptions']:
                    package_data['PackageServiceOptions'] = {}
                package_data['PackageServiceOptions']['DeliveryConfirmation'] = {
                    'DCISType':  signature_required,
                }
            res.append(package_data)
        return res

    package_type = self.carrier.ups_default_package_type_id
    return [{
        "Description": picking.name,
        "NumOfPieces": str(NumOfPieces),
        "Packaging": {
            "Code": package_type.shipper_package_code,
            "Description": package_type.name,
        },
        "Dimensions": {
            "UnitOfMeasurement": {"Code": self.package_dimension_code},
            "Length": str(package_type.packaging_length),
            "Width": str(package_type.width),
            "Height": str(package_type.height),
        },
        "PackageWeight": {
            "UnitOfMeasurement": {"Code": self.package_weight_code},
            "Weight": str(PackageWeight),
        },
        # TODO add signature requirements...
        "PackageServiceOptions": "",
    }]

def _prepare_create_shipping(self, picking, package=None):
    _logger.warning('_prepare_create_shipping(%s, %s)' % (picking, package))
    """Return a dict that can be passed to the shipping endpoint of the UPS API"""
    
    # setup some request level account details
    self.shipper_number = self.carrier._get_main_ups_account_number(picking=picking)
    
    if not package:
        package = picking.package_ids
    packages = []
    if package:
        packages = self._quant_package_data(package, picking)
    else:
        _logger.warning('  NOT COMPLETE _prepare_create_shipping')
        packages = []
        package_info = self._quant_package_data_from_picking(
            self.default_packaging_id, picking, False
        )
        package_weight = round(
            (picking.shipping_weight / picking.number_of_packages), 2
        )
        for i in range(0, picking.number_of_packages):
            package_item = package_info
            package_name = "%s (%s)" % (picking.name, i + 1)
            package_item["Description"] = package_name
            package_item["NumOfPieces"] = "1"
            package_item["Packaging"]["Description"] = package_name
            package_item["PackageWeight"]["Weight"] = str(package_weight)
            packages.append(package_item)
    
    res = {
        "ShipmentRequest": {
            "Shipment": {
                "Description": picking.name,
                "Shipper": self._partner_to_shipping_data(
                    partner=picking.company_id.partner_id,
                    ShipperNumber=self.shipper_number,
                ),
                "ShipTo": self._partner_to_shipping_data(picking.partner_id),
                "ShipFrom": self._partner_to_shipping_data(
                    picking.picking_type_id.warehouse_id.partner_id
                    or picking.company_id.partner_id
                ),
                "PaymentInformation": {
                    "ShipmentCharge": {
                        "Type": "01",
                        "BillShipper": {
                            "AccountNumber": self.shipper_number,
                        },
                    }
                },
                "Service": {"Code": self.service_code},
                "Package": packages,
            },
            "LabelSpecification": self._label_data(),
        }
    }
    
    ups_carrier_account = self.carrier._get_ups_carrier_account(picking)
    if ups_carrier_account:
        # del res['ShipmentRequest']['Shipment']['PaymentInformation']['ShipmentCharge']['BillShipper']
        # res['ShipmentRequest']['Shipment']['PaymentInformation']['ShipmentCharge']['Type'] = '02'
        res['ShipmentRequest']['Shipment']['PaymentInformation']['ShipmentCharge'] = {
            'Type': '01',
            'BillReceiver': {
                'Address': self._partner_to_shipping_data(picking.partner_id),
                'AccountNumber': ups_carrier_account,
            }
        }
        # TODO do we need to change the BillReceiver.Address.PostalCode ?
    _logger.warning('    ' + str(res))
    return res

UpsRequest._prepare_create_shipping = _prepare_create_shipping
UpsRequest._quant_package_data = _quant_package_data
