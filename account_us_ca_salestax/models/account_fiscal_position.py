from odoo import api, fields, models
from .ca_tax_request import CATaxRequest


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    is_us_ca = fields.Boolean(string='Use CA State API')
    ca_base_tax_id = fields.Many2one('account.tax', string='CA Base/Error Tax', company_dependent=True)

    @api.multi
    def map_tax(self, taxes, product=None, partner=None):

        if not taxes or not self.is_us_ca or partner is None:
            return super(AccountFiscalPosition, self).map_tax(taxes)

        AccountTax = self.env['account.tax'].sudo()
        result = AccountTax.browse()

        for tax in taxes:
            ca_tax = None
            request = CATaxRequest()
            try:
                res = request.get_rate(partner)
                ca_tax = AccountTax.search([
                    ('company_id', '=', self.ca_base_tax_id.company_id.id),
                    ('ca_county', '=', res['county']),
                    ('amount', '=', res['rate']),
                    ('amount_type', '=', 'percent'),
                    ('type_tax_use', '=', 'sale')], limit=1)
                if not ca_tax:
                    ca_tax = AccountTax.create({
                        'name': '%s - Tax %0.2f%%' % (res['county'], res['rate']),
                        'ca_county': res['county'],
                        'amount': res['rate'],
                        'amount_type': 'percent',
                        'type_tax_use': 'sale',
                        'account_id': self.ca_base_tax_id.account_id.id,
                        'refund_account_id': self.ca_base_tax_id.refund_account_id.id,
                        'company_id': self.ca_base_tax_id.company_id.id,
                        'ca_location_zips': partner.zip,
                    })
            except:
                ca_tax = AccountTax.search([
                    ('ca_location_zips', 'like', '%' + partner.zip + '%'),
                    ('amount_type', '=', 'percent'),
                    ('type_tax_use', '=', 'sale')], limit=1)
                if not ca_tax:
                    result |= self.ca_base_tax_id
                    continue

            if not ca_tax.ca_location_zips:
                ca_tax.write({'ca_location_zips': partner.zip})
            elif not ca_tax.ca_location_zips.find(str(partner.zip)) >= 0:
                zips = ca_tax.ca_location_zips.split(',')
                zips.append(str(partner.zip))
                ca_tax.write({'ca_location_zips': ','.join(zips)})

            # step 3: Find or create mapping
            tax_line = self.tax_ids.filtered(lambda x: x.tax_src_id.id == tax.id and x.tax_dest_id.id == ca_tax.id)
            if not tax_line:
                tax_line = self.env['account.fiscal.position.tax'].sudo().create({
                    'position_id': self.id,
                    'tax_src_id': tax.id,
                    'tax_dest_id': ca_tax.id,
                })

            result |= tax_line.tax_dest_id
        return result


class AccountTax(models.Model):
    _inherit = 'account.tax'

    ca_county = fields.Char('CA County')
    ca_location_zips = fields.Char('CA Location ZIPs', default='')
