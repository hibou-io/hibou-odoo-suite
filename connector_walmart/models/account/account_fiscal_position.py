# © 2017,2018 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from logging import getLogger

_logger = getLogger(__name__)


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    is_connector_walmart = fields.Boolean(string='Use Walmart Order Item Rate')

    @api.multi
    def map_tax(self, taxes, product=None, partner=None, order_line=None):

        if not taxes or not self.is_connector_walmart:
            return super(AccountFiscalPosition, self).map_tax(taxes, product=product, partner=partner)

        AccountTax = self.env['account.tax'].sudo()
        result = AccountTax.browse()

        for tax in taxes:
            if not order_line:
                raise ValidationError('Walmart Connector fiscal position requires order item details.')

            if not order_line.walmart_bind_ids:
                if order_line.price_unit == 0.0:
                    continue
                else:
                    raise ValidationError('Walmart Connector fiscal position requires Walmart Order Lines')

            tax_rate = order_line.walmart_bind_ids[0].tax_rate

            if tax_rate == 0.0:
                continue

            # step 1: Check if we already have this rate.
            tax_line = self.tax_ids.filtered(lambda x: tax_rate == x.tax_dest_id.amount and x.tax_src_id.id == tax.id)
            if not tax_line:
                #step 2: find or create this tax and tax_line
                new_tax = AccountTax.search([
                    ('name', 'like', 'Walmart %'),
                    ('amount', '=', tax_rate),
                    ('amount_type', '=', 'percent'),
                    ('type_tax_use', '=', 'sale'),
                ], limit=1)
                if not new_tax:
                    new_tax = AccountTax.create({
                        'name': 'Walmart Tax %0.2f %%' % (tax_rate,),
                        'amount': tax_rate,
                        'amount_type': 'percent',
                        'type_tax_use': 'sale',
                        'account_id': tax.account_id.id,
                        'refund_account_id': tax.refund_account_id.id,
                    })
                tax_line = self.env['account.fiscal.position.tax'].sudo().create({
                    'position_id': self.id,
                    'tax_src_id': tax.id,
                    'tax_dest_id': new_tax.id,
                })

            # step 3: map the tax
            result |= tax_line.tax_dest_id
        return result
