# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class ExceptionRule(models.Model):
    _inherit = 'exception.rule'

    model = fields.Selection(
        selection_add=[
            ('account.move', 'Journal Entry'),
        ],
        ondelete={
            'account.move': 'cascade',
        },
    )
    journal_entry_ids = fields.Many2many(
        'account.move',
        string="Journal Entries")


class AccountMove(models.Model):
    _inherit = ['account.move', 'base.exception']
    _name = "account.move"

    @api.model
    def _reverse_field(self):
        return 'journal_entry_ids'

    @api.model
    def _get_popup_action(self):
        return self.env.ref('account_exception.action_account_move_exception_confirm')

    def action_post(self):
        if len(self) == 1:
            if self.detect_exceptions():
                return self._popup_exceptions()
            else:
                return super().action_post()
        else:
            moves_with_exceptions = self.filtered(lambda m: m.detect_exceptions())
            other_moves = self - moves_with_exceptions
            return super(AccountMove, other_moves).action_post()
        return False
