from base64 import b64decode
from odoo import fields, models, _
from odoo.exceptions import UserError
from .purolator_services import PurolatorClient
import logging


_logger = logging.getLogger(__name__)

# 2022-09-21 - US Methods are known to rate, but cannot ship without additional customs/documents
PUROLATOR_SERVICES = [
    ('PurolatorExpress9AM', 'Purolator Express 9AM'),
    ('PurolatorExpress10:30AM', 'Purolator Express 10:30AM'),
    ('PurolatorExpress12PM', 'Purolator Express 12PM'),
    ('PurolatorExpress', 'Purolator Express'),
    ('PurolatorExpressEvening', 'Purolator Express Evening'),
    ('PurolatorExpressEnvelope9AM', 'Purolator Express Envelope 9AM'),
    ('PurolatorExpressEnvelope10:30AM', 'Purolator Express Envelope 10:30AM'),
    ('PurolatorExpressEnvelope12PM', 'Purolator Express Envelope 12PM'),
    ('PurolatorExpressEnvelope', 'Purolator Express Envelope'),
    ('PurolatorExpressEnvelopeEvening', 'Purolator Express Envelope Evening'),
    ('PurolatorExpressPack9AM', 'Purolator Express Pack 9AM'),
    ('PurolatorExpressPack10:30AM', 'Purolator Express Pack 10:30AM'),
    ('PurolatorExpressPack12PM', 'Purolator Express Pack 12PM'),
    ('PurolatorExpressPack', 'Purolator Express Pack'),
    ('PurolatorExpressPackEvening', 'Purolator Express Pack Evening'),
    ('PurolatorExpressBox9AM', 'Purolator Express Box 9AM'),
    ('PurolatorExpressBox10:30AM', 'Purolator Express Box 10:30AM'),
    ('PurolatorExpressBox12PM', 'Purolator Express Box 12PM'),
    ('PurolatorExpressBox', 'Purolator Express Box'),
    ('PurolatorExpressBoxEvening', 'Purolator Express Box Evening'),
    ('PurolatorGround', 'Purolator Ground'),
    ('PurolatorGround9AM', 'Purolator Ground 9AM'),
    ('PurolatorGround10:30AM', 'Purolator Ground 10:30AM'),
    ('PurolatorGroundEvening', 'Purolator Ground Evening'),
    ('PurolatorQuickShip', 'Purolator Quick Ship'),
    ('PurolatorQuickShipEnvelope', 'Purolator Quick Ship Envelope'),
    ('PurolatorQuickShipPack', 'Purolator Quick Ship Pack'),
    ('PurolatorQuickShipBox', 'Purolator Quick Ship Box'),
    # 2022-09-21 - US Methods are known to rate, but cannot ship without additional customs/documents
    # ('PurolatorExpressU.S.', 'Purolator Express U.S.'),
    # ('PurolatorExpressU.S.9AM', 'Purolator Express U.S. 9AM'),
    # ('PurolatorExpressU.S.10:30AM', 'Purolator Express U.S. 10:30AM'),
    # ('PurolatorExpressU.S.12:00', 'Purolator Express U.S. 12:00'),
    # ('PurolatorExpressEnvelopeU.S.', 'Purolator Express Envelope U.S.'),
    # ('PurolatorExpressU.S.Envelope9AM', 'Purolator Express U.S. Envelope 9AM'),
    # ('PurolatorExpressU.S.Envelope10:30AM', 'Purolator Express U.S. Envelope 10:30AM'),
    # ('PurolatorExpressU.S.Envelope12:00', 'Purolator Express U.S. Envelope 12:00'),
    # ('PurolatorExpressPackU.S.', 'Purolator Express Pack U.S.'),
    # ('PurolatorExpressU.S.Pack9AM', 'Purolator Express U.S. Pack 9AM'),
    # ('PurolatorExpressU.S.Pack10:30AM', 'Purolator Express U.S. Pack 10:30AM'),
    # ('PurolatorExpressU.S.Pack12:00', 'Purolator Express U.S. Pack 12:00'),
    # ('PurolatorExpressBoxU.S.', 'Purolator Express Box U.S.'),
    # ('PurolatorExpressU.S.Box9AM', 'Purolator Express U.S. Box 9AM'),
    # ('PurolatorExpressU.S.Box10:30AM', 'Purolator Express U.S. Box 10:30AM'),
    # ('PurolatorExpressU.S.Box12:00', 'Purolator Express U.S. Box 12:00'),
    # ('PurolatorGroundU.S.', 'Purolator Ground U.S.'),
    # 2022-09-21 - International Methods are known to rate
    # ('PurolatorExpressInternational', 'Purolator Express International'),
    # ('PurolatorExpressInternational9AM', 'Purolator Express International 9AM'),
    # ('PurolatorExpressInternational10:30AM', 'Purolator Express International 10:30AM'),
    # ('PurolatorExpressInternational12:00', 'Purolator Express International 12:00'),
    # ('PurolatorExpressEnvelopeInternational', 'Purolator Express Envelope International'),
    # ('PurolatorExpressInternationalEnvelope9AM', 'Purolator Express International Envelope 9AM'),
    # ('PurolatorExpressInternationalEnvelope10:30AM', 'Purolator Express International Envelope 10:30AM'),
    # ('PurolatorExpressInternationalEnvelope12:00', 'Purolator Express International Envelope 12:00'),
    # ('PurolatorExpressPackInternational', 'Purolator Express Pack International'),
    # ('PurolatorExpressInternationalPack9AM', 'Purolator Express International Pack 9AM'),
    # ('PurolatorExpressInternationalPack10:30AM', 'Purolator Express International Pack 10:30AM'),
    # ('PurolatorExpressInternationalPack12:00', 'Purolator Express International Pack 12:00'),
    # ('PurolatorExpressBoxInternational', 'Purolator Express Box International'),
    # ('PurolatorExpressInternationalBox9AM', 'Purolator Express International Box 9AM'),
    # ('PurolatorExpressInternationalBox10:30AM', 'Purolator Express International Box 10:30AM'),
    # ('PurolatorExpressInternationalBox12:00', 'Purolator Express International Box 12:00'),
]


class ProviderPurolator(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('purolator', 'Purolator')], 
                                     ondelete={'purolator': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0})})
    purolator_api_key = fields.Char(string='Purolator API Key', groups='base.group_system')
    purolator_password = fields.Char(string='Purolator Password', groups='base.group_system')
    purolator_activation_key = fields.Char(string='Purolator Activation Key', groups='base.group_system')
    purolator_account_number = fields.Char(string='Purolator Account Number', groups='base.group_system')
    purolator_service_type = fields.Selection(selection=PUROLATOR_SERVICES,
                                              default='PurolatorGround')
    purolator_default_package_type_id = fields.Many2one('stock.package.type', string="Purolator Package Type")
    purolator_label_file_type = fields.Selection([
            ('PDF', 'PDF'),
            ('ZPL', 'ZPL'),
        ], default='ZPL', string="Purolator Label File Type")
    
    def purolator_convert_weight(self, weight):
        weight_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        return weight_uom_id._compute_quantity(weight, self.env.ref('uom.product_uom_lb'), round=False)
    
    def purolator_convert_length(self, length):
        raise Exception('Not implemented. Need to do math on UOM to convert less dimensions')
        volume_uom_id = self.env['product.template']._get_volume_uom_id_from_ir_config_parameter()
        return volume_uom_id._compute_quantity(weight, self.env.ref('uom.product_uom_lb'), round=False)

    def purolator_rate_shipment(self, order, downgrade_response=True):
        multi_res = self._purolator_rate_shipment_multi_package(order=order)
        for res in multi_res:
            if res.get('carrier') == self:
                if downgrade_response:
                    return {
                        'success': res.get('success', True), 
                        'price': res.get('price', 0.0),
                        'error_message': res.get('error_message', False),
                        'warning_message': res.get('warning_message', False),
                    }
                return res
        return {
            'success': False,
            'price': 0.0,
            'error_message': _('No rate found matching service: %s') % self.purolator_service_type,
            'warning_message': False,
        }
    
    def purolator_rate_shipment_multi(self, order=None, picking=None, packages=None):
        if not packages:
            return self._purolator_rate_shipment_multi_package(order=order, picking=picking)
        else:
            rates = []
            for package in packages:
                rates += self._purolator_rate_shipment_multi_package(order=order, picking=picking, package=package)
            return rates
    
    def _purolator_format_errors(self, response_body, raise_class=None):
        errors = response_body.ResponseInformation.Errors
        if errors:
            errors = errors.Error  # unpack container node
            puro_errors = ['%s - %s - %s' % (e.Code, e.AdditionalInformation, e.Description) for e in errors]
            if raise_class:
                raise raise_class(_('Error(s) during Purolator Request:\n%s') % ('\n\n'.join(puro_errors), ))
            return puro_errors
    
    def _purolator_shipment_fill_payor(self, request, picking=None, order=None):
        request.PaymentInformation.PaymentType = 'Sender'
        request.PaymentInformation.RegisteredAccountNumber = self.purolator_account_number
        request.PaymentInformation.BillingAccountNumber = self.purolator_account_number
        third_party_account = self.purolator_third_party(picking=picking, order=order)
        # when would it be 'Receiver' ?
        if third_party_account:
            request.PaymentInformation.PaymentType = 'ThirdParty'
            request.PaymentInformation.BillingAccountNumber = third_party_account
    
    def _purolator_shipment_fill_options(self, request, picking=None, order=None, packages=None):
        # Signature can come from any package/packages
        require_signature = False
        if packages:
            # if ANY package has it
            require_signature = any(packages.mapped('require_signature'))
        else:
            require_signature = self.get_signature_required(order=order, picking=picking)
        # when we support international, there is also ResidentialSignatureIntl  (and AdultSignatureRequired)
        request.ResidentialSignatureDomestic = 'true' if require_signature else 'false'
        
        declared_value = 0.0
        if packages:
            declared_value = sum(s or 0.0 for s in packages.mapped('declared_value'))
        else:
            declared_value = self.get_insurance_value(picking=picking, order=order)
        if declared_value:
            request.DeclaredValue = str(round(declared_value, 2))
        
        request.DeclaredValue = str(self.get_insurance_value())
        # _logger.info('  _purolator_shipment_fill_options set sig.req. %s set declared val. %s' % (require_signature, declared_value))
        
    def _purolator_rate_shipment_multi_package(self, order=None, picking=None, package=None):
        service = self._purolator_service()
        third_party = self.purolator_third_party(order=order, picking=picking)
        sender = self.get_shipper_warehouse(order=order, picking=picking)
        receiver = self.get_recipient(order=order, picking=picking)
        
        date_planned = fields.Datetime.now()
        if self.env.context.get('date_planned'):
            date_planned = self.env.context.get('date_planned')
        
        # create SOAP request to fill in
        shipment = service.estimate_shipment_request()
        # request getting more than one service back
        shipment.ShowAlternativeServicesIndicator = "true"
        # indicate when we will ship this for time in transit
        shipment.ShipmentDate = str(date_planned)
        if hasattr(date_planned, 'date'):
            shipment.ShipmentDate = str(date_planned.date())
        
        # populate origin information
        self._purolator_fill_address(shipment.SenderInformation.Address, sender)
        # populate destination
        self._purolator_fill_address(shipment.ReceiverInformation.Address, receiver)
        
        if order:
            service.estimate_shipment_add_sale_order_packages(shipment, self, order)
        else:
            service.estimate_shipment_add_picking_packages(shipment, self, picking, package)
        
        self._purolator_shipment_fill_payor(shipment, order=order, picking=picking)
        self._purolator_shipment_fill_options(shipment, order=order, picking=picking, packages=package)
        
        shipment_res = service.get_full_estimate(shipment)
        
        # _logger.info('_purolator_rate_shipment_multi_package called with shipment %s result %s' % (shipment, shipment_res))

        errors = self._purolator_format_errors(shipment_res)
        if errors:
            return [{'carrier': self,
                     'success': False,
                     'price': 0.0,
                     'error_message': '\n'.join(errors),
                     'warning_message': False,
                    }]
        rates = []
        for shipment in shipment_res.ShipmentEstimates.ShipmentEstimate:
            carrier = self.purolator_find_delivery_carrier_for_service(shipment['ServiceID'])
            if carrier:
                price = shipment['TotalPrice']
                rates.append({
                    'carrier': carrier,
                    'package': package or self.env['stock.quant.package'].browse(),
                    'success': True,
                    'price': price if not third_party else 0.0,
                    'error_message': False,
                    'warning_message': _('TotalCharge not found.') if price == 0.0 else False,
                    'date_planned': date_planned,
                    'date_delivered': fields.Datetime.to_datetime(shipment['ExpectedDeliveryDate']),
                    'transit_days': shipment['EstimatedTransitDays'],
                    'service_code': shipment['ServiceID'],
                })
            
        return rates
    
    def purolator_find_delivery_carrier_for_service(self, service_code):
        if self.purolator_service_type == service_code:
            return self
        carrier = self.search([('delivery_type', '=', 'purolator'),
                               ('purolator_service_type', '=', service_code),
                               ('purolator_account_number', '=', self.purolator_account_number),
                               ], limit=1)
        return carrier
    
    def purolator_third_party(self, order=None, picking=None):
        third_party_account = self.get_third_party_account(order=order, picking=picking)
        if third_party_account:
            if not third_party_account.delivery_type == 'purolator':
                raise ValidationError('Non-Purolator Shipping Account indicated during Purolator shipment.')
            return third_party_account.name
        return False
    
    def _purolator_service(self):
        return PurolatorClient(
            self.purolator_api_key,
            self.purolator_password,
            self.purolator_activation_key,
            self.purolator_account_number,
            self.prod_environment,
        )

    def _purolator_address_street(self, partner):
        # assume we don't have base_address_extended
        street = partner.street or ''
        street_pieces = [t.strip() for t in street.split(' ')]
        len_street_pieces = len(street_pieces)
        if len_street_pieces >= 3:
            street_num = street_pieces[0]
            street_type = street_pieces[2]
            # TODO santize the types?  I see an example for "Douglas Road" that sends "Street"
            return street_num, ' '.join(street_pieces[1:]), 'Street'
        elif len_street_pieces == 2:
            return street_pieces[0], street_pieces[1], 'Street'
        return '', street, 'Street'

    def _purolator_address_phonenumber(self, partner):
        # TODO parse out of partner.phone or one of the many other phone numbers
        return '1', '905', '5555555'
        

    def _purolator_fill_address(self, addr, partner):
        # known to not work without a name
        addr.Name = partner.name
        addr.Company = partner.name if partner.is_company else (partner.company_name or '')
        addr.Department = ''
        addr.StreetNumber, addr.StreetName, addr.StreetType = self._purolator_address_street(partner)
        # addr.City = partner.city.upper() if partner.city else ''
        addr.City = partner.city or ''
        addr.Province = partner.state_id.code
        addr.Country = partner.country_id.code
        addr.PostalCode = partner.zip
        addr.PhoneNumber.CountryCode, addr.PhoneNumber.AreaCode, addr.PhoneNumber.Phone = self._purolator_address_phonenumber(partner)
    
    def _purolator_extract_doc_blobs(self, documents_result):
        res = []
        for d in getattr(documents_result.Documents, 'Document', []):
            for d2 in getattr(d.DocumentDetails, 'DocumentDetail', []):
                res.append(d2.Data)
        return res

    # Picking Shipping
    def purolator_send_shipping(self, pickings):
        res = []
        service = self._purolator_service()

        for picking in pickings:
            picking_packages = self.get_to_ship_picking_packages(picking)
            if picking_packages is None:
                continue
            
            shipment = service.shipment_request()
            
            # populate origin information
            sender = self.get_shipper_warehouse(picking=picking)
            self._purolator_fill_address(shipment.SenderInformation.Address, sender)
            
            receiver = self.get_recipient(picking=picking)
            self._purolator_fill_address(shipment.ReceiverInformation.Address, receiver)
            
            service.shipment_add_picking_packages(shipment, self, picking, picking_packages)
            
            self._purolator_shipment_fill_payor(shipment, picking=picking)
            self._purolator_shipment_fill_options(shipment, picking=picking, packages=picking_packages)
            
            shipment_res = service.shipment_create(shipment,
                                                   printer_type=('Regular' if self.purolator_label_file_type == 'PDF' else 'Thermal'))
            # _logger.info('purolator service.shipment_create for shipment %s resulted in %s' % (shipment, shipment_res))
            
            # this will raise an error alerting the user if there is an error, and no more
            self._purolator_format_errors(shipment_res, raise_class=UserError)
            
            document_blobs = []
            shipment_pin = shipment_res.ShipmentPIN.Value
            if picking_packages and getattr(shipment_res, 'PiecePINs', None):
                piece_pins = shipment_res.PiecePINs.PIN
                for p, pin in zip(picking_packages, piece_pins):
                    pin = pin.Value
                    p.carrier_tracking_ref = pin
                    doc_res = service.document_by_pin(pin, output_type=self.purolator_label_file_type)
                    for n, blob in enumerate(self._purolator_extract_doc_blobs(doc_res), 1):
                        document_blobs.append(('PuroPackage-%s-%s.%s' % (pin, n, self.purolator_label_file_type), b64decode(blob)))
            else:
                # retrieve shipment_pin document(s)
                doc_res = service.document_by_pin(shipment_pin, output_type=self.purolator_label_file_type)
                # _logger.info('purolator service.document_by_pin for pin %s resulted in %s' % (shipment_pin, doc_res))
                for n, blob in enumerate(self._purolator_extract_doc_blobs(doc_res), 1):
                    document_blobs.append(('PuroShipment-%s-%s.%s' % (shipment_pin, n, self.purolator_label_file_type), b64decode(blob)))
                
            if document_blobs:
                logmessage = _("Shipment created in Purolator <br/> <b>Tracking Number/PIN : </b>%s") % (shipment_pin)
                picking.message_post(body=logmessage, attachments=document_blobs)
            
            picking.carrier_tracking_ref = shipment_pin
            shipping_data = {
                'exact_price': picking.carrier_price, # price is set during planning
                'tracking_number': shipment_pin,
            }
            res.append(shipping_data)
        
        return res

    def purolator_get_tracking_link(self, pickings):
        res = []
        for picking in pickings:
            ref = picking.carrier_tracking_ref
            res = res + ['https://www.purolator.com/en/shipping/tracker?pins=%s' % ref]
        return res

    def purolator_cancel_shipment(self, picking, packages=None):
        service = self._purolator_service()
        if packages:
            for package in packages:
                tracking_pin = package.carrier_tracking_ref
                void_res = service.shipment_void(tracking_pin)
                self._purolator_format_errors(void_res, raise_class=UserError)
                package.write({'carrier_tracking_ref': ''})
                picking.message_post(body=_('Package N° %s has been cancelled' % tracking_pin))
        else:
            tracking_pin = picking.carrier_tracking_ref
            void_res = service.shipment_void(tracking_pin)
            self._purolator_format_errors(void_res, raise_class=UserError)
            picking.message_post(body=_('Shipment N° %s has been cancelled' % tracking_pin))
        picking.write({'carrier_tracking_ref': '',
                        'carrier_price': 0.0})
