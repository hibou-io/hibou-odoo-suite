from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestAccount(TransactionCase):
    
    def setUp(self):
        super(TestAccount, self).setUp()
        self.PartnerShippingAccount = self.env['partner.shipping.account']
        self.partner = self.env.ref('base.res_partner_12')
    
    def test_ups_account_information(self):
        # Create object and confirm that validation error raises if ups account number is blank or not 8 digits
        with self.assertRaises(ValidationError):
            wrong_account_number = self.PartnerShippingAccount.create({
                'name':          '1234567',
                'description':   'Error Account',
                'partner_id':    self.partner.id,
                'delivery_type': 'ups',
                'note':          'This is a note',
                'ups_zip':       '12345'
            })
        
        with self.assertRaises(ValidationError):
            no_account_number = self.PartnerShippingAccount.create({
                'name':          '',
                'description':   'Error Account',
                'partner_id':    self.partner.id,
                'delivery_type': 'ups',
                'note':          'This is a note',
                'ups_zip':       '12345'
            })
        # Create object and confirm that validation error raises if zipcode is blank or not 5 digits
        with self.assertRaises(ValidationError):
            wrong_zip_code = self.PartnerShippingAccount.create({
                'name':          '123456',
                'description':   'Error Account',
                'partner_id':    self.partner.id,
                'delivery_type': 'ups',
                'note':          'This is a note',
                'ups_zip':       '1234'
            })
        
        with self.assertRaises(ValidationError):
            no_zip_code = self.PartnerShippingAccount.create({
                'name':          '123456',
                'description':   'Error Account',
                'partner_id':    self.partner.id,
                'delivery_type': 'ups',
                'note':          'This is a note',
                'ups_zip':       ''
            })

        _ = self.PartnerShippingAccount.create({
            'name':          '123456',
            'description':   'Error Account',
            'partner_id':    self.partner.id,
            'delivery_type': 'ups',
            'note':          'This is a note',
            'ups_zip':       '12345'
        })
