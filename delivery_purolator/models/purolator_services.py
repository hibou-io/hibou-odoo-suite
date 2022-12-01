from math import ceil
from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep.cache import SqliteCache
from zeep.transports import Transport
from odoo.exceptions import UserError


PUROLATOR_PIECE_SPECIAL_HANDLING_TYPE = [
    # 'AdditionalHandling',  # unknown if this is "SpecialHandling"
    'FlatPackage',
    'LargePackage',
    # 'Oversized',  # unknown if this is "SpecialHandling"
    # 'ResidentialAreaHeavyweight',  # unknown if this is "SpecialHandling"
]


class PurolatorClient(object):
    
    # clients and factories
    _estimating_client = None
    @property
    def estimating_client(self):
        if not self._estimating_client:
            self._estimating_client = self._get_client('/EWS/V2/Estimating/EstimatingService.asmx?wsdl',
                                                       request_reference='Rating')
        return self._estimating_client
    
    _estimating_factory = None
    @property
    def estimating_factory(self):
        if not self._estimating_factory:
            self._estimating_factory = self.estimating_client.type_factory('ns1')
        return self._estimating_factory
    
    _shipping_client = None
    @property
    def shipping_client(self):
        if not self._shipping_client:
            self._shipping_client = self._get_client('/EWS/V2/Shipping/ShippingService.asmx?wsdl',
                                                     request_reference='Shipping')
        return self._shipping_client

    _shipping_factory = None
    @property
    def shipping_factory(self):
        if not self._shipping_factory:
            self._shipping_factory = self.shipping_client.type_factory('ns1')
        return self._shipping_factory

    _shipping_documents_client = None
    @property
    def shipping_documents_client(self):
        if not self._shipping_documents_client:
            self._shipping_documents_client = self._get_client('/PWS/V1/ShippingDocuments/ShippingDocumentsService.asmx?wsdl',
                                                               version='1.3',
                                                               request_reference='ShippingDocuments')
        return self._shipping_documents_client

    _shipping_documents_factory = None
    @property
    def shipping_documents_factory(self):
        if not self._shipping_documents_factory:
            self._shipping_documents_factory = self.shipping_documents_client.type_factory('ns1')
        return self._shipping_documents_factory
    
    def __init__(self, api_key, password, activation_key, account_number, is_prod):
        self.api_key = api_key
        self.password = password
        self.activation_key = activation_key
        self.account_number = account_number
        self._wsdl_base = "https://devwebservices.purolator.com"
        if is_prod:
            self._wsdl_base = "https://webservices.purolator.com"
            
        session = Session()
        session.auth = HTTPBasicAuth(self.api_key, self.password)
        self.transport = Transport(cache=SqliteCache(), session=session)
        
    def _get_client(self, wsdl_path, version='2.0', request_reference='RatingExample'):
        # version added because shipping documents needs a different one
        client = Client(self._wsdl_base + wsdl_path,
                        transport=self.transport)
        request_context = client.get_element('ns1:RequestContext')
        header_value = request_context(
            Version=version,
            Language='en',
            GroupID='xxx',  # TODO should we have a GroupID?
            RequestReference=request_reference,
            UserToken=self.activation_key,
        )
        client.set_default_soapheaders([header_value])
        return client
    
    def get_full_estimate(self, shipment, show_alternative_services='true'):
        response = self.estimating_client.service.GetFullEstimate(
            Shipment=shipment,
            ShowAlternativeServicesIndicator=show_alternative_services,
        )
        return response.body
            
    def get_quick_estimate(self, sender_postal_code, receiver_address, package_type, total_weight):
        """ Call GetQuickEstimate
        
        :param sender_postal_code: string
        :param receiver_address: dict {'City': string,
                                       'Province': string,
                                       'Country': string,
                                       'PostalCode': string}
        :param package_type: string
        :param total_weight: float (in pounds)
        :returns: dict {'shipments': list, 'error': string or False}
        """
        response = self.estimating_client.service.GetQuickEstimate(
            BillingAccountNumber=self.account_number,
            SenderPostalCode=sender_postal_code,
            ReceiverAddress=receiver_address,
            PackageType=package_type,
            TotalWeight={
                'Value': total_weight,
                'WeightUnit': 'lb',
            },
            )
        errors = response['body']['ResponseInformation']['Errors']
        if errors:
            return {
                'shipments': False,
                'error': '\n'.join(['%s: %s' % (error['Code'], error['Description']) for error in errors['Error']]),
            }
        shipments = response['body']['ShipmentEstimates']['ShipmentEstimate']
        if shipments:
            return {
                'shipments': shipments,
                'error': False,
            }
        return {
            'shipments': False,
            'error': 'Purolator service did not return any matching rates.',
        }
        
    def shipment_request(self):
        return self._shipment_request(self.shipping_factory)
    
    # just like above, but using estimate api
    def estimate_shipment_request(self):
        return self._shipment_request(self.estimating_factory)
    
    def _shipment_request(self, factory):
        shipment = factory.Shipment()
        shipment.SenderInformation = factory.SenderInformation()
        shipment.SenderInformation.Address = factory.Address()
        shipment.SenderInformation.Address.PhoneNumber = factory.PhoneNumber()
        shipment.ReceiverInformation = factory.ReceiverInformation()
        shipment.ReceiverInformation.Address = factory.Address()
        shipment.ReceiverInformation.Address.PhoneNumber = factory.PhoneNumber()
        shipment.PackageInformation = factory.PackageInformation()
        shipment.PackageInformation.TotalWeight = factory.TotalWeight()
        shipment.PackageInformation.PiecesInformation = factory.ArrayOfPiece()
        shipment.PaymentInformation = factory.PaymentInformation()
        return shipment
    
    def _add_piece_code(self, factory, piece, code):
        # note that we ONLY support special handling type
        if not piece.Options:
            piece.Options = factory.ArrayOfOptionIDValuePair()
            piece.Options.OptionIDValuePair.append(factory.OptionIDValuePair(
                ID='SpecialHandling',
                Value='true',
            ))
        piece.Options.OptionIDValuePair.append(factory.OptionIDValuePair(
            ID='SpecialHandlingType',
            Value=code,
        ))
    
    def estimate_shipment_add_sale_order_packages(self, shipment, carrier, order):
        # this could be a non-purolator package type as returned by the search functions
        package_type = carrier.get_package_type_for_order(order)
        total_pieces = carrier.get_package_count_for_order(order, package_type)
        
        package_type_codes = [t.strip() for t in (package_type.shipper_package_code or '').split(',') if t.strip() in PUROLATOR_PIECE_SPECIAL_HANDLING_TYPE]
        shipment.PackageInformation.ServiceID = carrier.purolator_service_type
        total_weight_value = carrier.purolator_convert_weight(order._get_estimated_weight())
        package_weight = total_weight_value / total_pieces
        if total_weight_value < 1.0:
            total_weight_value = 1.0
        if package_weight < 1.0:
            package_weight = 1.0

        for _i in range(total_pieces):
            p = self.estimating_factory.Piece(
                Weight={
                    'Value': str(package_weight),
                    'WeightUnit': 'lb',
                },
                Length={
                    'Value': str(package_type.packaging_length),  # TODO need conversion
                    'DimensionUnit': 'in', 
                },
                Width={
                    'Value': str(package_type.width),  # TODO need conversion
                    'DimensionUnit': 'in', 
                },
                Height={
                    'Value': str(package_type.height),  # TODO need conversion
                    'DimensionUnit': 'in', 
                },
            )
            for package_code in package_type_codes:
                self._add_piece_code(self.estimating_factory, p, package_code)
                
            shipment.PackageInformation.PiecesInformation.Piece.append(p)
        shipment.PackageInformation.TotalWeight.Value = str(total_weight_value)
        shipment.PackageInformation.TotalWeight.WeightUnit = 'lb'
        shipment.PackageInformation.TotalPieces = str(total_pieces)

    def estimate_shipment_add_picking_packages(self, shipment, carrier, picking, packages):    
        return self._shipment_add_picking_packages(self.estimating_factory, shipment, carrier, picking, packages)

    def shipment_add_picking_packages(self, shipment, carrier, picking, packages):    
        return self._shipment_add_picking_packages(self.shipping_factory, shipment, carrier, picking, packages)
    
    def _shipment_add_picking_packages(self, factory, shipment, carrier, picking, packages):
        # note that no package can be less than 1lb, so we fix that here...
        # for the package to be allowed, it must be the same service
        shipment.PackageInformation.ServiceID = carrier.purolator_service_type
        
        total_weight_value = 0.0
        total_pieces = len(packages or []) or 1
        if not packages:
            # setup default package
            package_weight = carrier.purolator_convert_weight(picking.shipping_weight)
            if package_weight < 1.0:
                package_weight = 1.0
            total_weight_value += package_weight
            package_type = carrier.purolator_default_package_type_id
            package_type_codes = [t.strip() for t in (package_type.shipper_package_code or '').split(',') if t.strip() in PUROLATOR_PIECE_SPECIAL_HANDLING_TYPE]
            p = factory.Piece(
                Weight={
                    'Value': str(package_weight),
                    'WeightUnit': 'lb',
                },
                Length={
                    'Value': str(package_type.packaging_length),  # TODO need conversion
                    'DimensionUnit': 'in', 
                },
                Width={
                    'Value': str(package_type.width),  # TODO need conversion
                    'DimensionUnit': 'in', 
                },
                Height={
                    'Value': str(package_type.height),  # TODO need conversion
                    'DimensionUnit': 'in', 
                },
            )
            for package_code in package_type_codes:
                self._add_piece_code(factory, p, package_code)
                
            shipment.PackageInformation.PiecesInformation.Piece.append(p)
        else:
            for package in packages:
                package_weight = carrier.purolator_convert_weight(package.shipping_weight)
                if package_weight < 1.0:
                    package_weight = 1.0
                package_type = package.package_type_id
                package_type_code = package_type.shipper_package_code or ''
                if package_type.package_carrier_type != 'purolator':
                    package_type_code = carrier.purolator_default_package_type_id.shipper_package_code or ''
                package_type_codes = [t.strip() for t in package_type_code.split(',') if t.strip() in PUROLATOR_PIECE_SPECIAL_HANDLING_TYPE]
                
                total_weight_value += package_weight
                p = factory.Piece(
                    Weight={
                        'Value': str(package_weight),
                        'WeightUnit': 'lb',
                    },
                    Length={
                        'Value': str(package_type.packaging_length),  # TODO need conversion
                        'DimensionUnit': 'in', 
                    },
                    Width={
                        'Value': str(package_type.width),  # TODO need conversion
                        'DimensionUnit': 'in', 
                    },
                    Height={
                        'Value': str(package_type.height),  # TODO need conversion
                        'DimensionUnit': 'in', 
                    },
                )
                for package_code in package_type_codes:
                    self._add_piece_code(factory, p, package_code)
                
                shipment.PackageInformation.PiecesInformation.Piece.append(p)
        
        shipment.PackageInformation.TotalWeight.Value = str(total_weight_value)
        shipment.PackageInformation.TotalWeight.WeightUnit = 'lb'
        shipment.PackageInformation.TotalPieces = str(total_pieces)

    def shipment_create(self, shipment, printer_type='Thermal'):
        response = self.shipping_client.service.CreateShipment(
            Shipment=shipment,
            PrinterType=printer_type,
        )
        return response.body
    
    def shipment_void(self, pin):
        response = self.shipping_client.service.VoidShipment(
            PIN={'Value': pin}
        )
        return response.body
    
    def document_by_pin(self, pin, document_type='', output_type='ZPL'):
        # TODO document_type?
        document_criterium = self.shipping_documents_factory.ArrayOfDocumentCriteria()
        document_criterium.DocumentCriteria.append(self.shipping_documents_factory.DocumentCriteria(
            PIN=pin,
        ))
        response = self.shipping_documents_client.service.GetDocuments(
            DocumentCriterium=document_criterium,
            OutputType=output_type,
            Synchronous=True,
        )
        return response.body
