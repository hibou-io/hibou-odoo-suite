from odoo import fields, models


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    allow_in_website_sale = fields.Boolean('Allow in website checkout')
