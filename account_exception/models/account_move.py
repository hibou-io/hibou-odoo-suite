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
    _order = 'main_exception_id asc, date desc, name desc, id desc'

    @api.model
    def _exception_rule_eval_context(self, rec):
        res = super(AccountMove, self)._exception_rule_eval_context(rec)
        res['journal_entry'] = rec
        return res

    @api.model
    def _reverse_field(self):
        return 'journal_entry_ids'

    @api.model
    def _get_popup_action(self):
        return self.env.ref('account_exception.action_account_move_exception_confirm')

    def write(self, vals):
        print(f'\n\nwrite()\ncontext={self._context}\n')
        newState = vals.get('state', '')
        if not vals.get('ignore_exception'):
            for journal_entry in self:
                if journal_entry.with_context(newState=newState).detect_exceptions():
                    return self._popup_exceptions()
        return super().write(vals)

    def detect_exceptions(self):
        print(f'\n\ndetect_exceptions()\ncontext={self._context}\n')
        res = False
        if not self._context.get("detect_exceptions"):
            self = self.with_context(detect_exceptions=True)
            res = super(AccountMove, self).detect_exceptions()
        return res
