from odoo import api, models
from odoo.addons.mail.models.mail_template import format_amount


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_invoice_id')
    def _onchange_partner_invoice_id(self):
        for so in self:
            partner = so.partner_invoice_id.commercial_partner_id
            if partner.credit_limit and partner.credit_limit <= partner.credit:
                m = 'Partner outstanding receivables %s is above their credit limit of %s' \
                                           % (format_amount(self.env, partner.credit, so.currency_id),
                                              format_amount(self.env, partner.credit_limit, so.currency_id))
                return {
                    'warning': {'title': 'Sale Credit Limit',
                                'message': m}
                }
