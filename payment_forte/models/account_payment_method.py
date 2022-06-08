from odoo import api, models, fields

class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    forte_type = fields.Selection([
        ('echeck', 'eCheck'),
        ('creditcard', 'Credit Card'),
    ])

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res['forte'] = {'mode': 'unique', 'domain': [('type', '=', 'bank')]}
        return res
