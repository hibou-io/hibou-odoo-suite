from odoo import api, fields, models
from odoo.exceptions import ValidationError
from .forte_request import ForteAPI
from json import dumps


def forte_get_api(acquirer):
    return ForteAPI(acquirer.forte_organization_id,
                    acquirer.forte_access_id,
                    acquirer.forte_secure_key,
                    acquirer.state)


class PaymentAcquirerForte(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('forte', 'Forte')],
                                ondelete={'forte': 'set default'})
    forte_organization_id = fields.Char(string='Organization ID')
    forte_location_id = fields.Char(string='Location ID')  # Probably move to Journal...
    forte_access_id = fields.Char(string='Access ID')
    forte_secure_key = fields.Char(string='Secure Key')

    def _get_feature_support(self):
        """Get advanced feature support by provider.

        Each provider should add its technical in the corresponding
        key for the following features:
            * fees: support payment fees computations
            * authorize: support authorizing payment (separates
                         authorization and capture)
            * tokenize: support saving payment data in a payment.tokenize
                        object
        """
        res = super(PaymentAcquirerForte, self)._get_feature_support()
        res['authorize'].append('authorize')
        res['tokenize'].append('authorize')
        return res

    def forte_test_credentials(self):
        self.ensure_one()
        api = forte_get_api(self)
        resp = api.test_authenticate()
        if not resp.ok:
            result = resp.json()
            if result and result.get('response'):
                raise ValidationError('Error: ' + dumps(result.get('response')))
        return True


class TxForte(models.Model):
    _inherit = 'payment.transaction'
    
    def _send_payment_request(self):
        """ Override of payment to send a payment request to Authorize.

        Note: self.ensure_one()

        :return: None
        :raise: UserError if the transaction is not linked to a token
        """
        
        super()._send_payment_request()
        if self.provider != 'forte':
            return

        self.ensure_one()
        api = forte_get_api(self.acquirer_id)
        location = self.acquirer_id.forte_location_id
        amount = self.amount
            
        account_type = self.token_id.forte_account_type
        routing_number = self.token_id.forte_routing_number
        account_number = self.token_id.forte_account_number
        account_holder = self.token_id.forte_account_holder
        
        method = self.payment_id.payment_method_id
        # if not self.env.context.get('payment_type'):
        if not method or not method.payment_type:
            _logger.warning('Trying to do a payment with Forte and no contextual payment_type will result in an inbound transaction.')
        # if self.env.context.get('payment_type') == 'inbound':
        if method.forte_type == 'echeck':
            if method.payment_type == 'outbound':
                resp = api.echeck_credit(location, amount, account_type, routing_number, account_number, account_holder)
            else:
                resp = api.echeck_sale(location, amount, account_type, routing_number, account_number, account_holder)
        # elif method.forte_type == 'creditcard':

        if resp.ok and resp.json()['response']['response_desc'] == 'APPROVED':
            ref = resp.json()['response']['authorization_code']
            return self.write({'state': 'done', 'acquirer_reference': ref})
        else:
            result = resp.json()
            if result and result.get('response'):
                raise ValidationError('Error: ' + dumps(result.get('response')))


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    forte_account_type = fields.Char(string='Forte Account Type', help='e.g. Checking')
    forte_routing_number = fields.Char(string='Forte Routing Number', help='e.g. 021000021')
    forte_account_number = fields.Char(string='Forte Account Number', help='e.g. 000111222')
    forte_account_holder = fields.Char(string='Forte Account Holder', help='e.g. John Doe')
