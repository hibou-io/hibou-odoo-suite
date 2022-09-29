# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    commission_ids = fields.One2many(comodel_name='hr.commission', inverse_name='source_move_id', string='Commissions')
    commission_count = fields.Integer(string='Number of Commissions', compute='_compute_commission_count')

    @api.depends('state', 'commission_ids')
    def _compute_commission_count(self):
        for move in self:
            move.commission_count = len(move.commission_ids)
        return True

    def open_commissions(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice Commissions',
            'res_model': 'hr.commission',
            'view_mode': 'tree,form',
            'context': {'search_default_source_move_id': self[0].id}
        }

    def action_post(self):
        res = super(AccountMove, self).action_post()
        invoices = self.filtered(lambda m: m.is_invoice())
        if invoices:
            self.env['hr.commission'].invoice_validated(invoices)
        return res

    def action_invoice_paid(self):
        res = super(AccountMove, self).action_invoice_paid()
        self.env['hr.commission'].invoice_paid(self)
        return res

    def amount_for_commission(self, commission=None):
        # Override to exclude ineligible products
        amount = 0.0
        if self.is_invoice():
            invoice_lines = self.invoice_line_ids.filtered(lambda l: not l.product_id.no_commission)
            if self.company_id.commission_amount_type == 'on_invoice_margin':
                margin_threshold = float(self.env['ir.config_parameter'].sudo().get_param('commission.margin.threshold', default=0.0))
                if margin_threshold:
                    invoice_lines = invoice_lines.filtered(lambda l: l.margin_percent > margin_threshold)
                sign = -1 if self.move_type in ['in_refund', 'out_refund'] else 1
                margin = sum(invoice_lines.mapped('margin'))
                amount = margin * sign
            else:
                amount = sum(invoice_lines.mapped('balance'))
                amount = abs(amount) if self.move_type == 'entry' else -amount
        return amount

    def action_cancel(self):
        res = super(AccountMove, self).action_cancel()
        for move in self:
            move.sudo().commission_ids.unlink()
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    margin_percent = fields.Float(string='Margin percent (%)', compute='_compute_margin_percent', digits=(3, 2))

    @api.depends('margin', 'product_id', 'purchase_price', 'quantity', 'price_unit', 'price_subtotal')
    def _compute_margin_percent(self):
        for line in self:
            currency = line.move_id.currency_id
            price = line.purchase_price
            if line.product_id and not price:
                date = line.move_id.date if line.move_id.date else fields.Date.context_today(line.move_id)
                from_cur = line.move_id.company_currency_id.with_context(date=date)
                price = from_cur._convert(line.product_id.standard_price, currency, line.company_id, date, round=False)
            total_price = price * line.quantity
            if total_price == 0.0:
                line.margin_percent = -1.0
            else:
                line.margin_percent = (line.margin / total_price) * 100.0
