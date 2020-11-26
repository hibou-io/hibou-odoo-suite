# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    pax_card_number = fields.Char(string='Card Number', help='Masked credit card.')
    pax_txn_id = fields.Char(string='PAX Transaction ID')


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    pos_use_pax = fields.Boolean(string='Use POS PAX Terminal',
                                 help='When used in POS, communicate with PAX Terminal for transactions.')


class PosConfig(models.Model):
    _inherit = 'pos.config'

    pax_endpoint = fields.Char(string='PAX Endpoint',
                               help='Endpoint for PAX device (include protocol (http or https) and port). '
                                    'e.g. http://192.168.1.101:10009')


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _payment_fields(self, ui_paymentline):
        fields = super(PosOrder, self)._payment_fields(ui_paymentline)

        fields.update({
            'pax_card_number': ui_paymentline.get('pax_card_number'),
            'pax_txn_id': ui_paymentline.get('pax_txn_id'),
        })

        return fields

    def add_payment(self, data):
        statement_id = super(PosOrder, self).add_payment(data)
        statement_lines = self.env['account.bank.statement.line'].search([('statement_id', '=', statement_id),
                                                                         ('pos_statement_id', '=', self.id),
                                                                         ('journal_id', '=', data['journal'])])
        statement_lines = statement_lines.filtered(lambda line: float_compare(line.amount, data['amount'],
                                                                              precision_rounding=line.journal_currency_id.rounding) == 0)

        # we can get multiple statement_lines when there are >1 credit
        # card payments with the same amount. In that case it doesn't
        # matter which statement line we pick, just pick one that
        # isn't already used.
        for line in statement_lines:
            if not line.pax_card_number:
                line.pax_card_number = data.get('pax_card_number')
                line.pax_txn_id = data.get('pax_txn_id')
                break

        return statement_id
