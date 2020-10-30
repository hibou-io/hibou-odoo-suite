from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare


class BarcodeRule(models.Model):
    _inherit = 'barcode.rule'

    type = fields.Selection(selection_add=[
        ('credit', 'Credit Card')
    ])


class CRMTeam(models.Model):
    _inherit = 'crm.team'

    pos_elavon_merchant_pin = fields.Char(string='POS Elavon Merchant PIN')


class PosElavonConfiguration(models.Model):
    _name = 'pos_elavon.configuration'

    name = fields.Char(required=True, help='Name of this Elavon configuration')
    merchant_id = fields.Char(string='Merchant ID', required=True, help='ID of the merchant to authenticate him on the payment provider server')
    merchant_user_id = fields.Char(string='Merchant User ID', required=True, help='User ID, e.g. POS')


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    elavon_card_number = fields.Char(string='Card Number', help='Masked credit card.')
    elavon_txn_id = fields.Char(string='Elavon Transaction ID')


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    pos_elavon_config_id = fields.Many2one('pos_elavon.configuration', string='Elavon Credentials',
                                            help='The configuration of Elavon that can be used with this journal.')


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _payment_fields(self, ui_paymentline):
        fields = super(PosOrder, self)._payment_fields(ui_paymentline)

        fields.update({
            'elavon_card_number': ui_paymentline.get('elavon_card_number'),
            'elavon_txn_id': ui_paymentline.get('elavon_txn_id'),
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
            if not line.elavon_card_number:
                line.elavon_card_number = data.get('elavon_card_number')
                line.elavon_txn_id = data.get('elavon_txn_id')
                break

        return statement_id


class AutoVacuum(models.AbstractModel):
    _inherit = 'ir.autovacuum'

    @api.model
    def power_on(self, *args, **kwargs):
        self.env['pos_elavon.elavon_transaction'].cleanup_old_tokens()
        return super(AutoVacuum, self).power_on(*args, **kwargs)
