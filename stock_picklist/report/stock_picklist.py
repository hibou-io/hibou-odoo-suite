from odoo import api, models
from collections import namedtuple

LocationGroup = namedtuple('LocationGroup', ('location_id', 'lines'))
ProductGroup = namedtuple('ProductGroup', ('product_id', 'qty'))


class StockPicklist(models.AbstractModel):
    _name = 'report.stock_picklist.report_picklist'
    _template = 'stock_picklist.report_picklist'

    @api.model
    def _get_report_values(self, docids, data=None):
        report_name = 'stock_picklist.report_picklist'
        report = self.env['ir.actions.report']._get_report_from_name(report_name)
        stock_pickings = self.env['stock.picking'].browse(docids)
        stock_pack_operations = stock_pickings.mapped(lambda o: o.move_lines).mapped(lambda l: l.move_line_ids)

        locations = stock_pack_operations.mapped(lambda o: o.location_id)
        _l = []
        for location in locations:
            operations = stock_pack_operations.filtered(lambda o: o.location_id.id == location.id)
            products = operations.mapped(lambda o: o.product_id)
            _p = []
            for product in products:
                qty = sum(operations.filtered(lambda o: o.product_id.id == product.id).mapped(lambda o: o.product_qty))
                _p.append(ProductGroup(product_id=product, qty=int(qty)))
            _p = sorted(_p, key=lambda p: -p.qty)
            _l.append(LocationGroup(location_id=location, lines=_p))

        _l = sorted(_l, key=lambda l: l.location_id.name)
        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': _l,
        }
