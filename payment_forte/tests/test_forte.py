from odoo.addons.payment.tests.common import PaymentCommon
from odoo.exceptions import ValidationError
from odoo.tests import tagged
class ForteCommon(PaymentCommon):
    
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.currency_usd = cls._prepare_currency('USD')
        cls.forte = cls._prepare_acquirer('forte', update_values={
            'fees_active': False, # Only activate fees in dedicated tests
            'forte_organization_id': '366035',
            'forte_location_id': '223008',
            'forte_access_id': 'a7b45fe9ff8d1d5406ae6f98791958da',
            'forte_secure_key': '20ee1d1f5a4afbf9db03af2c81f067c5',
        })

        # override defaults for helpers
        cls.acquirer = cls.forte
        cls.currency = cls.currency_usd
        cls.forte = cls.acquirer
        cls.method = cls.env.ref('payment_forte.payment_method_forte_echeck_inbound')
        cls.journal = cls.env['account.journal'].search([], limit=1)[0]
        cls.journal.write({
            'inbound_payment_method_line_ids': [(0, 0, {
                'name': 'Electronic',
                'payment_method_id': cls.method.id,
            })],
        })
        cls.method_line = cls.journal.inbound_payment_method_line_ids.filtered(lambda l: l.payment_method_id == cls.method)
        cls.buyer = cls.env['res.partner'].search([('customer_rank', '>=', 1)], limit=1)[0]


@tagged('post_install', '-at_install')
class ForteACH(ForteCommon):
    
    def test_10_forte_api(self):
        self.assertEqual(self.forte.state, 'test', 'Must test with test environment.')
        response = self.forte.forte_test_credentials()

        # Create/Save a Payment Token.
        # Change Token numbers to real values if you want to try to get an approval.
        token = self.env['payment.token'].create({
            'name': 'Test Token 1234',
            'partner_id': self.buyer.id,
            'acquirer_id': self.forte.id,
            'acquirer_ref': 'Test Token',
            'forte_account_type': 'Checking',
            'forte_routing_number': '021000021',
            'forte_account_number': '000111222',
            'forte_account_holder': self.buyer.name,
        })

        # Create Payment
        try:
            payment = self.env['account.payment'].create({
                'payment_type': 'inbound',
                'journal_id': self.journal.id,
                'partner_id': self.buyer.id,
                'payment_token_id': token.id,
                'payment_method_id': self.method.id,
                'payment_method_line_id': self.method_line.id,
                'amount': 22.00,
            })
            
            payment.action_post()
            self.assertTrue(payment.payment_transaction_id)
            self.assertEqual(payment.payment_transaction_id.amount, 22.00)
            self.assertTrue(payment.payment_transaction_id.acquirer_reference)
        except ValidationError as e:
            # U02 account not authorized.
            if e.name.find('U02') < 0:
                raise e
