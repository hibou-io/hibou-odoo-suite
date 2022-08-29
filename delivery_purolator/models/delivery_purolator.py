from odoo import fields, models, _
from .purolator_services import PurolatorClient


class ProviderPurolator(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('purolator', 'Purolator')], ondelete={'purolator': 'cascade'})
    purolator_api_key = fields.Char(string='Purolator API Key', groups='base.group_system')
    purolator_password = fields.Char(string='Purolator Password', groups='base.group_system')
    purolator_activation_key = fields.Char(string='Purolator Activation Key', groups='base.group_system')
    purolator_account_number = fields.Char(string='Purolator Account Number', groups='base.group_system')
    purolator_service_type = fields.Selection([('PurolatorExpress', 'PurolatorExpress')], default='PurolatorExpress')
    
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
        weight_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        weight = weight_uom_id._compute_quantity(order._get_estimated_weight(), self.env.ref('uom.product_uom_lb'), round=False)
        client = PurolatorClient(self)
        res = client.get_quick_estimate(sender.zip, receiver_address, 'CustomerPackaging', weight)
        if res['error']:
            return {
                'success': False,
                'price': 0.0,
                'error_message': _(res['error']),
                'warning_message': False,
            }
        return {
            'success': True, 
            'price': res['price'],
            'error_message': False,
            'warning_message': False,
        }
