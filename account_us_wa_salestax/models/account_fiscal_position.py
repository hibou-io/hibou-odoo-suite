# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from wa_tax_request import WATaxRequest


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    is_us_wa = fields.Boolean(string='Use WA State API')
    wa_base_tax_id = fields.Many2one('account.tax', string='WA Base/Error Tax')

    @api.multi
    def map_tax(self, taxes, product=None, partner=None):

        if not taxes or not self.is_us_wa or partner is None:
            return super(AccountFiscalPosition, self).map_tax(taxes)

        AccountTax = self.env['account.tax'].sudo()
        result = AccountTax.browse()

        for tax in taxes:
            # step 1: If we were to save the location code on the partner we might not have to do this
            request = WATaxRequest()
            res = request.get_rate(partner)
            wa_tax = None
            if not request.is_success(res):
                # Cache.
                wa_tax = AccountTax.search([
                    ('wa_location_zips', 'like', '%' + partner.zip + '%'),
                    ('amount_type', '=', 'percent'),
                    ('type_tax_use', '=', 'sale')], limit=1)
                if not wa_tax:
                    result |= self.wa_base_tax_id
                    continue

            # step 2: Find or create tax
            if not wa_tax:
                wa_tax = AccountTax.search([
                    ('wa_location_code', '=', res['location_code']),
                    ('amount', '=', res['rate']),
                    ('amount_type', '=', 'percent'),
                    ('type_tax_use', '=', 'sale')], limit=1)
            if not wa_tax:
                wa_tax = AccountTax.create({
                    'name': '%s - WA Tax %s %%' % (res['location_code'], res['rate']),
                    'wa_location_code': res['location_code'],
                    'amount': res['rate'],
                    'amount_type': 'percent',
                    'type_tax_use': 'sale',
                    'account_id': self.wa_base_tax_id.account_id.id,
                    'refund_account_id': self.wa_base_tax_id.refund_account_id.id
                })

            if not wa_tax.wa_location_zips:
                wa_tax.wa_location_zips = partner.zip
            elif not wa_tax.wa_location_zips.find(partner.zip) >= 0:
                zips = wa_tax.wa_location_zips.split(',')
                zips.append(partner.zip)
                wa_tax.wa_location_zips = zips.append(',')

            # step 3: Find or create mapping
            tax_line = self.tax_ids.filtered(lambda x: x.tax_src_id.id == tax.id and x.tax_dest_id.id == wa_tax.id)
            if not tax_line:
                tax_line = self.env['account.fiscal.position.tax'].sudo().create({
                    'position_id': self.id,
                    'tax_src_id': tax.id,
                    'tax_dest_id': wa_tax.id,
                })

            result |= tax_line.tax_dest_id
        return result

class AccountTax(models.Model):
    _inherit = 'account.tax'

    wa_location_code = fields.Integer('WA Location Code')
    wa_location_zips = fields.Char('WA Location ZIPs', default='')
