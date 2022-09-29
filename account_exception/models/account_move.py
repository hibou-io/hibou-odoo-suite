# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class ExceptionRule(models.Model):
    _inherit = 'exception.rule'

    model = fields.Selection(
        selection_add=[
            ('account.move', 'Invoice'),
        ],
        ondelete={
            'account.move': 'cascade',
        },
    )
    invoice_ids = fields.Many2many(
        'account.move',
        string="Invoices")

class AccountMove(models.Model):
    _inherit = ['account.move', 'base.exception']
    _name = "account.move"
    _order = 'main_exception_id asc, date desc, name desc, id desc'

    @api.model
    def _exception_rule_eval_context(self, rec):
        res = super(AccountMove, self)._exception_rule_eval_context(rec)
        res['invoice'] = rec
        return res

    @api.model
    def _reverse_field(self):
        return 'invoice_ids'

    def action_post(self):
        self.ensure_one()
        if self.detect_exceptions():
            return self._popup_exceptions()
        return super().action_post()
# TODO
    @api.model
    def _get_popup_action(self):
        return self.env.ref('stock_exception.action_stock_exception_confirm')

