from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestAccount(TransactionCase):
    
    def setUp(self):
        super(TestAccount, self).setUp()
        self.PartnerShippingAccount = self.env['partner.shipping.account']
        self.partner = self.env.ref('base.res_partner_12')
    
    def test_fedex_account_information(self):
        # Create object and confirm that validation error raises if fedex account is blank or not 8 digits
        with self.assertRaises(ValidationError):
            wrong_account_number = self.PartnerShippingAccount.create({
                'name':          '12345678',
                'description':   'Error Account',
                'partner_id':    self.partner.id,
                'delivery_type': 'fedex',
                'note':          'This is a note'
            })
        
        with self.assertRaises(ValidationError):
            no_account_number = self.PartnerShippingAccount.create({
                'name':          '',
                'description':   'Error Account',
                'partner_id':    self.partner.id,
                'delivery_type': 'fedex',
                'note':          'This is a note'
            })

        _ = self.PartnerShippingAccount.create({
            'name':          '123456789',
            'description':   'Error Account',
            'partner_id':    self.partner.id,
            'delivery_type': 'fedex',
            'note':          'This is a note'
        })
