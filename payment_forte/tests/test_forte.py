from json import dumps
from unittest import SkipTest
import logging

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.addons.payment.tests.common import PaymentCommon
from ..models.payment import forte_get_api


_logger = logging.getLogger(__name__)


class ForteCommon(PaymentCommon):
    
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        
        cls.forte = cls._prepare_acquirer('forte', update_values={
            'fees_active': False, # Only activate fees in dedicated tests
        })
        
        if not cls.forte.forte_secure_key:
            skip_message = 'Credentials have not been configured for Forte, skipping tests...'
            _logger.warning(skip_message)
            raise SkipTest(skip_message)

        # override defaults for helpers
        cls.acquirer = cls.forte
        cls.inbound_payment_method_line = cls.acquirer.journal_id.inbound_payment_method_line_ids.filtered(lambda l: l.code == 'forte')
        
    def forte_test_credentials(self):
        api = forte_get_api(self.acquirer)
        resp = api.test_authenticate()
        if not resp.ok:
            result = resp.json()
            if result and result.get('response'):
                raise ValidationError('Error: ' + dumps(result.get('response')))
        return True


@tagged('post_install', '-at_install')
class ForteACH(ForteCommon):
    
    def test_10_forte_api(self):
        self.assertEqual(self.forte.state, 'test', 'Must test with test environment.')
        self.assertTrue(self.forte_test_credentials())

        # Create/Save a Payment Token.
        # Change Token numbers to real values if you want to try to get an approval.
        token = self.create_token(
            forte_account_type='Checking',
            forte_routing_number='021000021',
            forte_account_number='000111222',
            forte_account_holder=self.partner.name,
        )

        # Create Payment
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'amount': 22.0,
            # 'date': '2019-01-01',
            'currency_id': self.currency.id,
            'partner_id': self.partner.id,
            'journal_id': self.acquirer.journal_id.id,
            'payment_method_line_id': self.inbound_payment_method_line.id,
            'payment_token_id': token.id,
        })
        
        payment.action_post()
        self.assertTrue(payment.payment_transaction_id)
        self.assertEqual(payment.payment_transaction_id.amount, 22.00)
        self.assertTrue(payment.payment_transaction_id.acquirer_reference)
