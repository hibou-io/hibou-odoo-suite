from odoo import api, fields, models
from math import ceil
from datetime import timedelta


class PurchaseBySaleHistory(models.TransientModel):
    _name = 'purchase.sale.history.make'

    purchase_id = fields.Many2one('purchase.order', string='Purchase Order')
    history_start = fields.Date(string='Sales History Start', default=lambda o: fields.Date.from_string(fields.Date.today()) - timedelta(days=30))
    history_end = fields.Date(string='Sales History End', default=fields.Date.today)
    history_days = fields.Integer(string='Sales History Days', compute='_compute_history_days')
    procure_days = fields.Integer(string='Days to Procure',
                                  default=30,
                                  help='History will be computed as an average per day, '
                                       'and then multiplied by the days you wish to procure for.')
    product_count = fields.Integer(string='Product Count', compute='_compute_product_count',
                                   help='Products on the PO or that the Vendor provides.')

    @api.multi
    @api.depends('history_start', 'history_end')
    def _compute_history_days(self):
        for wiz in self:
            if not all((wiz.history_end, wiz.history_start)):
                wiz.history_days = 0
            else:
                delta = fields.Date.from_string(wiz.history_end) - fields.Date.from_string(wiz.history_start)
                wiz.history_days = delta.days

    @api.multi
    @api.depends('purchase_id', 'purchase_id.order_line', 'purchase_id.partner_id')
    def _compute_product_count(self):
        for wiz in self:
            if wiz.purchase_id.order_line:
                wiz.product_count = len(set(wiz.purchase_id.order_line.mapped('product_id.id')))
            elif wiz.purchase_id.partner_id:
                self.env.cr.execute("""SELECT COUNT(DISTINCT(psi.product_id)) + COUNT(DISTINCT(p.id)) 
                                       FROM product_supplierinfo psi 
                                       LEFT JOIN product_product p ON p.product_tmpl_id = psi.product_tmpl_id AND psi.product_id IS NULL
                                       WHERE psi.name = %d;"""
                                    % (wiz.purchase_id.partner_id.id, ))
                wiz.product_count = self.env.cr.fetchall()[0][0]

    def _history_product_ids(self):
        if self.purchase_id.order_line:
            return self.purchase_id.order_line.mapped('product_id.id')

        self.env.cr.execute("""SELECT DISTINCT(COALESCE(psi.product_id, p.id))
                               FROM product_supplierinfo psi 
                               LEFT JOIN product_product p ON p.product_tmpl_id = psi.product_tmpl_id AND psi.product_id IS NULL
                               WHERE psi.name = %d;"""
                                    % (self.purchase_id.partner_id.id, ))
        rows = self.env.cr.fetchall()
        return [r[0] for r in rows if r[0]]

    def _sale_history(self, product_ids):
        self.env.cr.execute("""SELECT product_id, sum(product_uom_qty)
                               FROM sale_report 
                               WHERE date BETWEEN %s AND %s AND product_id IN %s
                               GROUP BY 1""", (self.history_start, self.history_end, tuple(product_ids)))
        return self.env.cr.fetchall()

    def _apply_history(self, history):
        line_model = self.env['purchase.order.line']
        updated_lines = line_model.browse()
        for pid, sold_qty in history:
            # TODO: Should convert from Sale UOM to Purchase UOM
            qty = ceil(sold_qty * self.procure_days / self.history_days)
            # Find line that already exists on PO
            line = self.purchase_id.order_line.filtered(lambda l: l.product_id.id == pid)
            if line:
                line.write({'product_qty': qty})
                line._onchange_quantity()
            else:
                # Create new PO line
                line = line_model.new({
                    'order_id': self.purchase_id.id,
                    'product_id': pid,
                    'product_qty': qty,
                })
                line.onchange_product_id()
                line_vals = line._convert_to_write(line._cache)
                line_vals['product_qty'] = qty
                line = line_model.create(line_vals)
            updated_lines += line

        # Lines not touched should now not be ordered.
        other_lines = self.purchase_id.order_line - updated_lines
        other_lines.write({'product_qty': 0.0})
        for line in other_lines:
            line._onchange_quantity()

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        history_product_ids = self._history_product_ids()
        history = self._sale_history(history_product_ids)
        self._apply_history(history)


