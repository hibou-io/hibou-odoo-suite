import logging
# from odoo.addons.stock.tests.test_move2 import TestPickShip
from odoo import fields
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestPicking(TransactionCase):
    def setUp(self):
        super(TestPicking, self).setUp()
        self.nominal_weight = 50.0
        self.partner1 = self.env.ref('base.res_partner_2')
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.ref_uom_id = self.env.ref('uom.product_uom_kgm')
        self.product_uom_id = self.env['uom.uom'].create({
            'name': '50 ref',
            'category_id': self.ref_uom_id.category_id.id,
            'uom_type': 'bigger',
            'factor_inv': self.nominal_weight,
        })
        self.product1 = self.env['product.product'].create({
            'name': 'Product 1',
            'type': 'product',
            'tracking': 'serial',
            'list_price': 100.0,
            'standard_price': 50.0,
            'taxes_id': [(5, 0, 0)],
            'uom_id': self.product_uom_id.id,
            'uom_po_id': self.product_uom_id.id,
            'catch_weight_uom_id': self.ref_uom_id.id,
        })
        self.pricelist = self.env.ref('product.list0')


    # def test_creation(self):
    #     self.productA.tracking = 'serial'
    #     lot = self.env['stock.lot'].create({
    #         'product_id': self.productA.id,
    #         'name': '123456789',
    #     })
    #
    #     lot.catch_weight_ratio = 0.8
    #     _logger.warn(lot.xxxcatch_weight_ratio)



    # def test_delivery(self):
    #     self.productA.tracking = 'serial'
    #     picking_pick, picking_pack, picking_ship = self.create_pick_pack_ship()
    #     stock_location = self.env['stock.location'].browse(self.stock_location)
    #     lot = self.env['stock.lot'].create({
    #         'product_id': self.productA.id,
    #         'name': '123456789',
    #         'catch_weight_ratio': 0.8,
    #     })
    #     self.env['stock.quant']._update_available_quantity(self.productA, stock_location, 1.0, lot_id=lot)

    def test_so_invoice(self):
        ref_weight = 45.0
        lot = self.env['stock.lot'].create({
            'product_id': self.product1.id,
            'name': '123456789',
            'catch_weight': ref_weight,
        })
        self.assertAlmostEqual(lot.catch_weight_ratio, ref_weight / self.nominal_weight)
        self.env['stock.quant']._update_available_quantity(self.product1, self.stock_location, 1.0, lot_id=lot)
        so = self.env['sale.order'].create({
            'partner_id': self.partner1.id,
            'partner_invoice_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
            'order_line': [(0, 0, {'product_id': self.product1.id})],
            'pricelist_id': self.pricelist.id,
        })
        so.action_confirm()
        self.assertTrue(so.state in ('sale', 'done'))
        self.assertEqual(len(so.picking_ids), 1)
        picking = so.picking_ids
        self.assertEqual(picking.state, 'assigned')
        self.assertEqual(picking.move_lines.move_line_ids.lot_id, lot)
        picking.move_lines.move_line_ids.qty_done = 1.0
        picking.button_validate()
        self.assertEqual(picking.state, 'done')

        inv_id = so.action_invoice_create()
        inv = self.env['account.invoice'].browse(inv_id)
        self.assertAlmostEqual(inv.amount_total, lot.catch_weight_ratio * self.product1.list_price)

    def test_so_invoice2(self):
        ref_weight1 = 45.0
        ref_weight2 = 51.0
        lot1 = self.env['stock.lot'].create({
            'product_id': self.product1.id,
            'name': '1-low',
            'catch_weight': ref_weight1,
        })
        lot2 = self.env['stock.lot'].create({
            'product_id': self.product1.id,
            'name': '1-high',
            'catch_weight': ref_weight2,
        })
        self.env['stock.quant']._update_available_quantity(self.product1, self.stock_location, 1.0, lot_id=lot1)
        self.env['stock.quant']._update_available_quantity(self.product1, self.stock_location, 1.0, lot_id=lot2)
        so = self.env['sale.order'].create({
            'partner_id': self.partner1.id,
            'partner_invoice_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
            'order_line': [(0, 0, {'product_id': self.product1.id, 'product_uom_qty': 2.0})],
            'pricelist_id': self.pricelist.id,
        })
        so.action_confirm()
        self.assertTrue(so.state in ('sale', 'done'))
        self.assertEqual(len(so.picking_ids), 1)
        picking = so.picking_ids
        self.assertEqual(picking.state, 'assigned')
        self.assertEqual(picking.move_lines.move_line_ids.mapped('lot_id'), lot1 + lot2)
        for line in picking.move_lines.move_line_ids:
            line.qty_done = 1.0
        picking.button_validate()
        self.assertEqual(picking.state, 'done')

        inv_id = so.action_invoice_create()
        inv = self.env['account.invoice'].browse(inv_id)
        self.assertAlmostEqual(inv.amount_total, self.product1.list_price * (lot1.catch_weight_ratio + lot2.catch_weight_ratio))

    def test_po_invoice(self):
        ref_weight1 = 45.0
        ref_weight2 = 51.0
        weights = (ref_weight1, ref_weight2)
        price = self.product1.standard_price
        po = self.env['purchase.order'].create({
            'partner_id': self.partner1.id,
            'order_line': [(0, 0, {
                'product_id': self.product1.id,
                'product_qty': 2.0,
                'name': 'Test',
                'date_planned': fields.Datetime.now(),
                'product_uom': self.product1.uom_po_id.id,
                'price_unit': price,
            })]
        })
        po.button_confirm()
        self.assertEqual(po.state, 'purchase')
        self.assertEqual(len(po.picking_ids), 1)

        picking = po.picking_ids
        for i, line in enumerate(picking.move_lines.move_line_ids):
            line.write({'lot_name': str(i), 'qty_done': 1.0, 'catch_weight': weights[i]})
        picking.button_validate()
        self.assertEqual(picking.state, 'done')

        inv = self.env['account.invoice'].create({
            'type': 'in_invoice',
            'partner_id': self.partner1.id,
            'purchase_id': po.id,
        })
        inv.purchase_order_change()
        self.assertEqual(len(inv.invoice_line_ids), 1)
        self.assertEqual(inv.invoice_line_ids.quantity, 2.0)
        self.assertAlmostEqual(inv.amount_total, price * sum(w / self.nominal_weight for w in weights))

