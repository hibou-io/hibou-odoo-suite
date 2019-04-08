from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    margin = fields.Float(compute='_product_margin', digits=dp.get_precision('Product Price'), store=True)
    purchase_price = fields.Float(string='Cost', digits=dp.get_precision('Product Price'))

    def _compute_margin(self, invoice_id, product_id, product_uom_id, sale_line_ids):
        # if sale_line_ids and don't re-browse
        for line in sale_line_ids:
            return line.purchase_price
        frm_cur = invoice_id.company_currency_id
        to_cur = invoice_id.currency_id
        purchase_price = product_id.standard_price
        if product_uom_id != product_id.uom_id:
            purchase_price = product_id.uom_id._compute_price(purchase_price, product_uom_id)
        ctx = self.env.context.copy()
        ctx['date'] = invoice_id.date if invoice_id.date else fields.Date.context_today(invoice_id)
        price = frm_cur.with_context(ctx)._convert(purchase_price, to_cur, invoice_id.company_id, ctx['date'], round=False)
        return price

    @api.onchange('product_id', 'uom_id')
    def product_id_change_margin(self):
        if not self.product_id or not self.uom_id:
            return
        self.purchase_price = self._compute_margin(self.invoice_id, self.product_id, self.uom_id, self.sale_line_ids)

    @api.model
    def create(self, vals):
        line = super(AccountInvoiceLine, self).create(vals)
        line.product_id_change_margin()
        return line

    @api.depends('product_id', 'purchase_price', 'quantity', 'price_unit', 'price_subtotal')
    def _product_margin(self):
        for line in self:
            currency = line.invoice_id.currency_id
            price = line.purchase_price
            if line.product_id and not price:
                date = line.invoice_id.date if line.invoice_id.date else fields.Date.context_today(line.invoice_id)
                from_cur = line.invoice_id.company_currency_id.with_context(date=date)
                price = from_cur._convert(line.product_id.standard_price, currency, line.company_id, date, round=False)
 
            line.margin = currency.round(line.price_subtotal - (price * line.quantity))


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    margin = fields.Monetary(compute='_product_margin',
                             help="It gives profitability by calculating the difference between the Unit Price and the cost.",
                             currency_field='currency_id',
                             digits=dp.get_precision('Product Price'),
                             store=True)

    @api.depends('invoice_line_ids.margin')
    def _product_margin(self):
        for invoice in self:
            invoice.margin = sum(invoice.invoice_line_ids.mapped('margin'))
