from odoo import fields, models, _
from .purolator_services import PurolatorClient
import logging


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
    ('PurolatorExpressU.S.', 'Purolator Express U.S.'),
    ('PurolatorExpressU.S.9AM', 'Purolator Express U.S. 9AM'),
    ('PurolatorExpressU.S.10:30AM', 'Purolator Express U.S. 10:30AM'),
    ('PurolatorExpressU.S.12:00', 'Purolator Express U.S. 12:00'),
    ('PurolatorExpressEnvelopeU.S.', 'Purolator Express Envelope U.S.'),
    ('PurolatorExpressU.S.Envelope9AM', 'Purolator Express U.S. Envelope 9AM'),
    ('PurolatorExpressU.S.Envelope10:30AM', 'Purolator Express U.S. Envelope 10:30AM'),
    ('PurolatorExpressU.S.Envelope12:00', 'Purolator Express U.S. Envelope 12:00'),
    ('PurolatorExpressPackU.S.', 'Purolator Express Pack U.S.'),
    ('PurolatorExpressU.S.Pack9AM', 'Purolator Express U.S. Pack 9AM'),
    ('PurolatorExpressU.S.Pack10:30AM', 'Purolator Express U.S. Pack 10:30AM'),
    ('PurolatorExpressU.S.Pack12:00', 'Purolator Express U.S. Pack 12:00'),
    ('PurolatorExpressBoxU.S.', 'Purolator Express Box U.S.'),
    ('PurolatorExpressU.S.Box9AM', 'Purolator Express U.S. Box 9AM'),
    ('PurolatorExpressU.S.Box10:30AM', 'Purolator Express U.S. Box 10:30AM'),
    ('PurolatorExpressU.S.Box12:00', 'Purolator Express U.S. Box 12:00'),
    ('PurolatorGroundU.S.', 'Purolator Ground U.S.'),
    ('PurolatorExpressInternational', 'Purolator Express International'),
    ('PurolatorExpressInternational9AM', 'Purolator Express International 9AM'),
    ('PurolatorExpressInternational10:30AM', 'Purolator Express International 10:30AM'),
    ('PurolatorExpressInternational12:00', 'Purolator Express International 12:00'),
    ('PurolatorExpressEnvelopeInternational', 'Purolator Express Envelope International'),
    ('PurolatorExpressInternationalEnvelope9AM', 'Purolator Express International Envelope 9AM'),
    ('PurolatorExpressInternationalEnvelope10:30AM', 'Purolator Express International Envelope 10:30AM'),
    ('PurolatorExpressInternationalEnvelope12:00', 'Purolator Express International Envelope 12:00'),
    ('PurolatorExpressPackInternational', 'Purolator Express Pack International'),
    ('PurolatorExpressInternationalPack9AM', 'Purolator Express International Pack 9AM'),
    ('PurolatorExpressInternationalPack10:30AM', 'Purolator Express International Pack 10:30AM'),
    ('PurolatorExpressInternationalPack12:00', 'Purolator Express International Pack 12:00'),
    ('PurolatorExpressBoxInternational', 'Purolator Express Box International'),
    ('PurolatorExpressInternationalBox9AM', 'Purolator Express International Box 9AM'),
    ('PurolatorExpressInternationalBox10:30AM', 'Purolator Express International Box 10:30AM'),
    ('PurolatorExpressInternationalBox12:00', 'Purolator Express International Box 12:00'),
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
    
    def _purolator_weight(self, weight):
        weight_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        return weight_uom_id._compute_quantity(weight, self.env.ref('uom.product_uom_lb'), round=False)

    def purolator_rate_shipment(self, order):
        # sudoself = self.sudo()
        sender = self.get_shipper_warehouse(order=order)
        receiver = self.get_recipient(order=order)
        receiver_address = {
            'City': receiver.city,
            'Province': receiver.state_id.code,
            'Country': receiver.country_id.code,
            'PostalCode': receiver.zip,
        }
        # TODO packaging volume/length/width/height
        weight = self._purolator_weight(order._get_estimated_weight())
        client = PurolatorClient(
            self.purolator_api_key,
            self.purolator_password,
            self.purolator_activation_key,
            self.purolator_account_number,
            self.prod_environment,
        )
        res = client.get_quick_estimate(
            sender.zip,
            receiver_address,
            self.purolator_default_package_type_id.shipper_package_code,
            weight,
        )
        if res['error']:
            return {
                'success': False,
                'price': 0.0,
                'error_message': _(res['error']),
                'warning_message': False,
            }
        shipment = list(filter(lambda s: s['ServiceID'] == self.purolator_service_type, res['shipments']))
        if not shipment:
            return {
                'success': False,
                'price': 0.0,
                'error_message': _('No rate found matching service: %s') % self.purolator_service_type,
                'warning_message': False,
            }
        return {
            'success': True, 
            'price': shipment[0]['TotalPrice'],
            'error_message': False,
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
    
    def _purolator_rate_shipment_multi_package(self, order=None, picking=None, package=None):
        sender = self.get_shipper_warehouse(order=order, picking=picking)
        receiver = self.get_recipient(order=order, picking=picking)
        receiver_address = {
            'City': receiver.city,
            'Province': receiver.state_id.code,
            'Country': receiver.country_id.code,
            'PostalCode': receiver.zip,
        }
        weight_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        volume_uom_id = self.env['product.template']._get_volume_uom_id_from_ir_config_parameter()
        
        date_planned = fields.Datetime.now()
        if self.env.context.get('date_planned'):
            date_planned = self.env.context.get('date_planned')
        
        # TODO need packaging volume/dimensions
        package_code = self.purolator_default_package_type_id.shipper_package_code
        if order:
            weight = order._get_estimated_weight()
        else:
            if package:
                weight = package.shipping_weight
                package_code = package.package_type_id.shipper_package_code if package.package_type_id.package_carrier_type == 'purolator' else package_code
            else:
                weight = picking.shipping_weight or picking.weight
        weight = self._purolator_weight(weight)
        client = PurolatorClient(
            self.purolator_api_key,
            self.purolator_password,
            self.purolator_activation_key,
            self.purolator_account_number,
            self.prod_environment,
        )
        res = client.get_quick_estimate(sender.zip, receiver_address, package_code, weight)
        if res['error']:
            return [{'carrier': self,
                     'success': False,
                     'price': 0.0,
                     'error_message': _('Error:\n%s') % res['error'],
                     'warning_message': False,
                    }]
        rates = []
        for shipment in res['shipments']:
            carrier = self.purolator_find_delivery_carrier_for_service(shipment['ServiceID'])
            if carrier:
                price = shipment['TotalPrice']
                rates.append({
                    'carrier': carrier,
                    'package': package or self.env['stock.quant.package'].browse(),
                    'success': True,
                    'price': price,
                    'error_message': False,
                    'warning_message': _('TotalCharge not found.') if price == 0.0 else False,
                    'date_planned': date_planned,
                    'date_delivered': fields.Date.to_date(shipment['ExpectedDeliveryDate']),
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

    # Picking Shipping
    def purolator_send_shipping(self, pickings):
        res = []
        # service = self._get_purolator_service()
        # had_customs = False

        for picking in pickings:
            picking_packages = self.get_to_ship_picking_packages(picking)
            if picking_packages is None:
                continue
            
            # do the shipment!
            package_labels = []
            for x in []:
                res = res + [shipping_data]  # bug! fill in with appropriate data
            picking.carrier_tracking_ref = ','.join(package_labels)
        
        # FIXME
        shipping_data = {'exact_price': 1.0,
                         'tracking_number': ''}
        res.append(shipping_data)
        return res
