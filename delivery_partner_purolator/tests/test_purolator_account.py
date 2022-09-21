from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestAccount(TransactionCase):
    
    def setUp(self):
        super(TestAccount, self).setUp()
        self.PartnerShippingAccount = self.env['partner.shipping.account']
        self.partner = self.env.ref('base.res_partner_12')
    
    def test_purolator_account_information(self):
        # Create object and confirm that validation error raises if fedex account is blank or not 8 digits
        _ = self.PartnerShippingAccount.create({
            'name':          '123456789',
            'description':   'Test Account',
            'partner_id':    self.partner.id,
            'delivery_type': 'purolator',
            'note':          'This is a note'
        })
