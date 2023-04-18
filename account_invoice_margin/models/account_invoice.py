from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    margin = fields.Monetary(compute='_compute_product_margin', digits='Product Price', store=True,
                             groups='base.group_user')
    margin_percent = fields.Float(compute='_product_margin', store=True, string='Margin (%)',
                                  groups='base.group_user')
    purchase_price = fields.Monetary(string='Cost', digits='Product Price',
                                     groups='base.group_user')

    # Note we are keeping this API because it is easy to customize and extend the purchase price/margin calculation
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
                line.purchase_price = 0.0
            else:
                line.purchase_price = line._compute_margin(line.move_id, line.product_id, line.product_uom_id, line.sale_line_ids)

    @api.model_create_multi
    def create(self, vals):
        lines = super(AccountMoveLine, self).create(vals)
        if vals and 'purchase_price' not in vals[0]:
            lines.product_id_change_margin()
        return lines

    @api.depends('product_id', 'purchase_price', 'quantity', 'price_unit', 'price_subtotal')
    def _compute_product_margin(self):
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
            line.margin_percent =  1.0 if not line.price_subtotal else line.margin / line.price_subtotal


class AccountMove(models.Model):
    _inherit = "account.move"

    margin = fields.Monetary(compute='_compute_product_margin', store=True, digits='Product Price',
                             help="Profitability by calculating the difference between the Unit Price and the cost.",
                             groups='base.group_user')
    margin_percent = fields.Float(compute='_compute_product_margin', store=True, string='Margin (%)',
                                  groups='base.group_user')

    @api.depends('invoice_line_ids.margin', 'invoice_line_ids.price_subtotal')
    def _compute_product_margin(self):
        for invoice in self:
            invoice.margin = sum(invoice.invoice_line_ids.mapped('margin'))
            total_price_subtotal = sum(invoice.invoice_line_ids.mapped('price_subtotal'))
            invoice.margin_percent = 1.0 if not total_price_subtotal else invoice.margin / total_price_subtotal
