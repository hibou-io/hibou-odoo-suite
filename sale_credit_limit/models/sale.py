# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, models, tools
from odoo.tools.safe_eval import datetime as wrapped_datetime


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # We need a way to be able to create a 'today' date to compare
    @api.model
    def _exception_rule_eval_context(self, rec):
        res = super(SaleOrder, self)._exception_rule_eval_context(rec)
        res["datetime"] = wrapped_datetime
        return res

    @api.onchange('partner_invoice_id')
    def _onchange_partner_invoice_id(self):
        for so in self:
            partner = so.partner_invoice_id.commercial_partner_id
            if partner.credit_limit and partner.credit_limit <= partner.credit:
                m = 'Partner outstanding receivables %s is above their credit limit of %s' \
                                           % (tools.format_amount(self.env, partner.credit, so.currency_id),
                                              tools.format_amount(self.env, partner.credit_limit, so.currency_id))
                return {
                    'warning': {'title': 'Sale Credit Limit',
                                'message': m}
                }
