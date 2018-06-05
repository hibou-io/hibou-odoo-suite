import logging
# from odoo.addons.stock.tests.test_move2 import TestPickShip
from odoo import fields
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestPicking(TransactionCase):
    def setUp(self):
        super(TestPicking, self).setUp()
        self.partner1 = self.env.ref('base.res_partner_2')
        self.product1 = self.env['product.product'].create({
            'name': 'Product 1',
            'type': 'product',
            'tracking': 'serial',
            'list_price': 100.0,
            'standard_price': 50.0,
            'taxes_id': [(5, 0, 0)],
        })
        #self.product1 = self.env.ref('product.product_order_01')
        self.product1.write({
            'type': 'product',
            'tracking': 'serial',
        })
        self.stock_location = self.env.ref('stock.stock_location_stock')


    # def test_creation(self):
    #     self.productA.tracking = 'serial'
    #     lot = self.env['stock.production.lot'].create({
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
    #     lot = self.env['stock.production.lot'].create({
    #         'product_id': self.productA.id,
    #         'name': '123456789',
    #         'catch_weight_ratio': 0.8,
    #     })
    #     self.env['stock.quant']._update_available_quantity(self.productA, stock_location, 1.0, lot_id=lot)

    def test_so_invoice(self):
        ratio = 0.8
        lot = self.env['stock.production.lot'].create({
            'product_id': self.product1.id,
            'name': '123456789',
            'catch_weight_ratio': ratio,
        })
        self.env['stock.quant']._update_available_quantity(self.product1, self.stock_location, 1.0, lot_id=lot)
        so = self.env['sale.order'].create({
            'partner_id': self.partner1.id,
            'partner_invoice_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
            'order_line': [(0, 0, {'product_id': self.product1.id})],
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
        self.assertEqual(inv.amount_total, ratio * self.product1.list_price)

    def test_so_invoice2(self):
        ratio1 = 0.8
        ratio2 = 1.1
        lot1 = self.env['stock.production.lot'].create({
            'product_id': self.product1.id,
            'name': '1-low',
            'catch_weight_ratio': ratio1,
        })
        lot2 = self.env['stock.production.lot'].create({
            'product_id': self.product1.id,
            'name': '1-high',
            'catch_weight_ratio': ratio2,
        })
        self.env['stock.quant']._update_available_quantity(self.product1, self.stock_location, 1.0, lot_id=lot1)
        self.env['stock.quant']._update_available_quantity(self.product1, self.stock_location, 1.0, lot_id=lot2)
        so = self.env['sale.order'].create({
            'partner_id': self.partner1.id,
            'partner_invoice_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
            'order_line': [(0, 0, {'product_id': self.product1.id, 'product_uom_qty': 2.0})],
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
        self.assertEqual(inv.amount_total, (ratio1 * self.product1.list_price) + (ratio2 * self.product1.list_price))

    def test_po_invoice(self):
        ratio1 = 0.8
        ratio2 = 1.1
        ratios = (ratio1, ratio2)
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
            line.write({'lot_name': str(i), 'qty_done': 1.0, 'lot_catch_weight_ratio': ratios[i]})
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
        self.assertEqual(inv.amount_total, (ratio1 * price) + (ratio2 * price))


