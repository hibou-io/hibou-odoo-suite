from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    margin = fields.Float(compute='_product_margin', digits='Product Price', store=True)
    purchase_price = fields.Float(string='Cost', digits='Product Price')

    def _compute_margin(self, move, product, product_uom, sale_lines):
        # if sale_line_ids and don't re-browse
        for line in sale_lines:
            return line.purchase_price
        frm_cur = move.company_currency_id
        to_cur = move.currency_id
        purchase_price = product.standard_price
        if product_uom and product_uom != product.uom_id:
            purchase_price = product.uom_id._compute_price(purchase_price, product_uom)
        ctx = self.env.context.copy()
        ctx['date'] = move.date if move.date else fields.Date.context_today(move)
        price = frm_cur.with_context(ctx)._convert(purchase_price, to_cur, move.company_id, ctx['date'], round=False)
        return price

    @api.onchange('product_id', 'product_uom_id')
    def product_id_change_margin(self):
        for line in self:
            if not line.product_id:
                return
            line.purchase_price = line._compute_margin(line.move_id, line.product_id, line.product_uom_id, line.sale_line_ids)

    @api.model_create_multi
    def create(self, vals):
        line = super(AccountMoveLine, self).create(vals)
        line.product_id_change_margin()
        return line

    @api.depends('product_id', 'purchase_price', 'quantity', 'price_unit', 'price_subtotal')
    def _product_margin(self):
        for line in self:
            currency = line.move_id.currency_id
            price = line.purchase_price
            margin = line.price_subtotal - (price * line.quantity)
            if line.product_id and not price:
                date = line.move_id.date if line.move_id.date else fields.Date.context_today(line.move_id)
                from_cur = line.move_id.company_currency_id.with_context(date=date)
                price = from_cur._convert(line.product_id.standard_price, currency, line.company_id, date, round=False)
                margin = line.price_subtotal - (price * line.quantity)
 
            line.margin = currency.round(margin) if currency else margin


class AccountMove(models.Model):
    _inherit = "account.move"

    margin = fields.Monetary(compute='_product_margin',
                             help="It gives profitability by calculating the difference between the Unit Price and the cost.",
                             currency_field='currency_id',
                             digits='Product Price',
                             store=True)

    @api.depends('invoice_line_ids.margin')
    def _product_margin(self):
        for invoice in self:
            invoice.margin = sum(invoice.invoice_line_ids.mapped('margin'))
