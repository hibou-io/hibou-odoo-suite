from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_invoice_id')
    def _onchange_partner_invoice_id(self):
        for so in self:
            partner = so.partner_invoice_id.commercial_partner_id
            if partner.credit_limit and partner.credit_limit <= partner.credit:
                m = 'Partner outstanding receivables %0.2f is above their credit limit of %0.2f' \
                                           % (partner.credit, partner.credit_limit)
                return {
                    'warning': {'title': 'Sale Credit Limit',
                                'message': m}
                }
