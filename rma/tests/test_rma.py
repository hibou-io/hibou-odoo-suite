# -*- coding: utf-8 -*-
from odoo.tests import common
from odoo.exceptions import UserError


class TestRMA(common.TransactionCase):
    def setUp(self):
        super(TestRMA, self).setUp()
        self.product1 = self.env.ref('product.product_product_24')
        self.template1 = self.env.ref('rma.template_missing_item')
        self.partner1 = self.env.ref('base.res_partner_2')

    def test_00_basic_rma(self):
        rma = self.env['rma.rma'].create({
            'template_id': self.template1.id,
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
        rma = self.env['rma.rma'].create({
            'template_id': self.template1.id,
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
