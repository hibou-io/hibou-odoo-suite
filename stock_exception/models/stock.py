# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, models, fields


class ExceptionRule(models.Model):
    _inherit = 'exception.rule'

    model = fields.Selection(
        selection_add=[
            ('stock.picking', 'Transfer'),
        ],
        ondelete={
            'stock.picking': 'cascade',
        },
    )
    picking_ids = fields.Many2many(
        'stock.picking',
        string="Transfers")

class Picking(models.Model):
    _inherit = ['stock.picking', 'base.exception']
    _name = 'stock.picking'
    _order = 'main_exception_id asc, priority desc, date asc, id desc'

    @api.model
    def _exception_rule_eval_context(self, rec):
        res = super(Picking, self)._exception_rule_eval_context(rec)
        res['picking'] = rec
        return res

    @api.model
    def _reverse_field(self):
        return 'picking_ids'

    def button_validate(self):
        self.ensure_one()
        if self.detect_exceptions():
            return self._popup_exceptions()
        return super().button_validate()

    @api.model
    def _get_popup_action(self):
        return self.env.ref('stock_exception.action_stock_exception_confirm')

