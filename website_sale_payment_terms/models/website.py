from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    payment_deposit_threshold = fields.Monetary(string='Payment Deposit Threshold',
                                                help='Allow customers to make a deposit when their order '
                                                     'total is above this amount.')

    def get_payment_terms(self):
        return self.env['account.payment.term'].search([('allow_in_website_sale', '=', True)])
