from odoo.addons.payment.tests.common import PaymentAcquirerCommon
from odoo.exceptions import ValidationError


class ForteCommon(PaymentAcquirerCommon):
    def setUp(self):
        super(ForteCommon, self).setUp()
        self.currency_usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)[0]
        self.forte = self.env.ref('payment.payment_acquirer_forte')
        self.method = self.env['account.payment.method'].search([('code', '=', 'electronic')], limit=1)[0]
        self.journal = self.env['account.journal'].search([], limit=1)[0]


class ForteACH(ForteCommon):
    def test_10_forte_api(self):
        self.assertEqual(self.forte.environment, 'test', 'Must test with test environment.')
        response = self.forte.forte_test_credentials()

        # Create/Save a Payment Token.
        # Change Token numbers to real values if you want to try to get an approval.
        token = self.env['payment.token'].create({
            'partner_id': self.buyer_id,
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
                'partner_id': self.buyer_id,
                'payment_token_id': token.id,
                'payment_method_id': self.method.id,
                'amount': 22.00,
            })
            self.assertEqual(payment.payment_transaction_id.amount, 22.00)
            self.assertTrue(payment.payment_transaction_id.acquirer_reference)
        except ValidationError as e:
            self.assertTrue(e.name.find('U02') >= 0)

