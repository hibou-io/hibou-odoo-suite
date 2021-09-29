from odoo import api, fields, models
from odoo.exceptions import UserError


class PurchaseBySaleHistory(models.TransientModel):
    _inherit = 'purchase.sale.history.make'

    def _apply_history_product(self, product, history):
        # Override to recursively collect sales and forcast for products produced by this product.
        bom_line_model = self.env['mrp.bom.line']
        product_model = self.env['product.product']
        if self.history_warehouse_ids:
            product_model = self.env['product.product'] \
                .with_context({'location': [wh.lot_stock_id.id for wh in self.history_warehouse_ids]})
        visited_product_ids = set()

        def bom_parent_product_ids(product):
            if product.id in visited_product_ids:
                # Cycle detected
                return 0.0
            visited_product_ids.add(product.id)

            bom_lines = bom_line_model.search([('product_id', '=', product.id), ('bom_id.active', '=', True)])
            if not bom_lines:
                # Recursive Basecase
                return 0.0

            product_ids = set()
            for line in bom_lines:
                product_ids |= bom_parent_product_ids_line(line)
            product_ids_dict = {}
            for pid, ratio in product_ids:
                if pid in product_ids_dict:
                    raise UserError('You cannot have two identical finished goods being created '
                                    'from different ratios/BoMs. Finished Product ID: %s' % (pid, ))
                product_ids_dict[pid] = {'ratio': ratio}
            if not product_ids_dict:
                # this indicates that the BOM is for a product.template without any product variants
                # if there are no variants, then it couldn't have been sold
                return 0.0

            history = self._sale_history(product_ids_dict.keys())
            products = product_model.browse(product_ids_dict.keys())

            for pid, sold_qty in history:
                product_ids_dict[pid]['sold_qty'] = sold_qty
            for p in products:
                qty = product_ids_dict[p.id].get('sold_qty', 0.0) * self.procure_days / self.history_days
                product_ids_dict[p.id]['buy_qty'] = max((0.0, qty - p.virtual_available))
                product_ids_dict[p.id]['buy_qty'] += bom_parent_product_ids(p)
                product_ids_dict[p.id]['buy_qty'] *= product_ids_dict[p.id].get('ratio', 1.0)

            return sum(vals['buy_qty'] for vals in product_ids_dict.values())

        def bom_parent_product_ids_line(line):
            product_ids = set()
            if line.bom_id.product_id:
                product_ids.add((line.bom_id.product_id.id, line.product_qty))
            else:
                for p in line.bom_id.product_tmpl_id.product_variant_ids:
                    product_ids.add((p.id, line.product_qty))
            return product_ids

        super(PurchaseBySaleHistory, self)._apply_history_product(product, history)
        history['buy_qty'] += bom_parent_product_ids(product)
