# -*- coding: utf-8 -*-
from odoo.tests import common
from odoo.exceptions import UserError


class TestRMA(common.TransactionCase):
    def setUp(self):
        super(TestRMA, self).setUp()
        self.product1 = self.env.ref('product.product_product_24')
        self.template_missing = self.env.ref('rma.template_missing_item')
        self.template_return = self.env.ref('rma.template_picking_return')
        self.partner1 = self.env.ref('base.res_partner_2')

    def test_00_basic_rma(self):
        self.template_missing.usage = False
        rma = self.env['rma.rma'].create({
            'template_id': self.template_missing.id,
            'partner_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
        })
        self.assertEqual(rma.state, 'draft')
        rma_line = self.env['rma.line'].create({
            'rma_id': rma.id,
            'product_id': self.product1.id,
            'product_uom_id': self.product1.uom_id.id,
            'product_uom_qty': 2.0,
        })
        rma.action_confirm()
        # Should have made pickings
        self.assertEqual(rma.state, 'confirmed')
        # No inbound picking
        self.assertFalse(rma.in_picking_id)
        # Good outbound picking
        self.assertTrue(rma.out_picking_id)
        self.assertEqual(rma_line.product_id, rma.out_picking_id.move_lines.product_id)
        self.assertEqual(rma_line.product_uom_qty, rma.out_picking_id.move_lines.product_uom_qty)

        with self.assertRaises(UserError):
            rma.action_done()

        rma.out_picking_id.action_done()
        rma.action_done()
        self.assertEqual(rma.state, 'done')

    def test_10_rma_cancel(self):
        self.template_missing.usage = False
        rma = self.env['rma.rma'].create({
            'template_id': self.template_missing.id,
            'partner_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
        })
        self.assertEqual(rma.state, 'draft')
        rma_line = self.env['rma.line'].create({
            'rma_id': rma.id,
            'product_id': self.product1.id,
            'product_uom_id': self.product1.uom_id.id,
            'product_uom_qty': 2.0,
        })
        rma.action_confirm()
        # Good outbound picking
        self.assertEqual(rma.out_picking_id.move_lines.state, 'assigned')
        rma.action_cancel()
        self.assertEqual(rma.out_picking_id.move_lines.state, 'cancel')

    def test_20_picking_rma(self):
        type_out = self.env.ref('stock.picking_type_out')
        location = self.env.ref('stock.stock_location_stock')
        location_customer = self.env.ref('stock.stock_location_customers')
        self.product1.tracking = 'serial'
        picking_out = self.env['stock.picking'].create({
            'partner_id': self.partner1.id,
            'name': 'testpicking',
            'picking_type_id': type_out.id,
            'location_id': location.id,
            'location_dest_id': location_customer.id,
        })
        self.env['stock.move'].create({
            'name': self.product1.name,
            'product_id': self.product1.id,
            'product_uom_qty': 1.0,
            'product_uom': self.product1.uom_id.id,
            'picking_id': picking_out.id,
            'location_id': location.id,
            'location_dest_id': location_customer.id,
        })
        picking_out.action_confirm()

        # Try to RMA item not delivered yet
        rma = self.env['rma.rma'].create({
            'template_id': self.template_return.id,
            'partner_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
            'stock_picking_id': picking_out.id,
        })
        self.assertEqual(rma.state, 'draft')
        wizard = self.env['rma.picking.make.lines'].create({
            'rma_id': rma.id,
        })
        wizard.line_ids.product_uom_qty = 1.0
        wizard.add_lines()
        self.assertEqual(len(rma.lines), 1)
        with self.assertRaises(UserError):
            rma.action_confirm()

        picking_out.force_assign()
        pack_opt = self.env['stock.pack.operation'].search([('picking_id', '=', picking_out.id)], limit=1)
        lot = self.env['stock.production.lot'].create({'product_id': self.product1.id, 'name': 'X100'})
        self.env['stock.pack.operation.lot'].create({'operation_id': pack_opt.id, 'lot_id': lot.id, 'qty': 1.0})
        pack_opt.qty_done = 1.0
        picking_out.do_transfer()

        self.assertEqual(picking_out.state, 'done')

        rma.action_confirm()
        self.assertEqual(rma.in_picking_id.state, 'assigned')
        pack_opt = self.env['stock.pack.operation'].search([('picking_id', '=', rma.in_picking_id.id)], limit=1)
        self.assertEqual(pack_opt.pack_lot_ids.lot_id, lot)

        with self.assertRaises(UserError):
            rma.action_done()

        pack_opt.pack_lot_ids.qty = 1.0
        pack_opt.qty_done = 1.0
        rma.in_picking_id.do_transfer()
        rma.action_done()

        # Make another RMA for the same picking
        rma2 = self.env['rma.rma'].create({
            'template_id': self.template_return.id,
            'partner_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
            'stock_picking_id': picking_out.id,
        })
        wizard = self.env['rma.picking.make.lines'].create({
            'rma_id': rma2.id,
        })
        wizard.line_ids.product_uom_qty = 1.0
        wizard.add_lines()
        self.assertEqual(len(rma2.lines), 1)

        rma2.action_confirm()
        # Inbound picking is in state confirmed (Waiting Availability) since it reuses picking
        self.assertEqual(rma2.in_picking_id.state, 'confirmed')
        # RMA cannot be completed because the inbound picking state is confirmed
        with self.assertRaises(UserError):
            rma2.action_done()
