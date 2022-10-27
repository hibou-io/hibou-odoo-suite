from odoo.tests import common
from odoo.exceptions import ValidationError


class TestSaleLineChange(common.TransactionCase):
    def setUp(self):
        super(TestSaleLineChange, self).setUp()
        self.warehouse0 = self.env.ref('stock.warehouse0')
        self.warehouse1 = self.env['stock.warehouse'].create({
            'company_id': self.env.user.company_id.id,
            # 'partner_id': self.env.user.company_id.partner_id.id,
            'name': 'TWH1',
            'code': 'TWH1',
        })
        self.product1 = self.env.ref('product.product_product_24')
        self.partner1 = self.env.ref('base.res_partner_12')
        self.so1 = self.env['sale.order'].create({
            'partner_id': self.partner1.id,
            'partner_invoice_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
            'order_line': [(0, 0, {
                'product_id': self.product1.id,
                'name': 'N/A',
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })]
        })
        self.dropship_route = self.env.ref('stock_dropshipping.route_drop_shipping')
        self.warehouse0_route = self.warehouse0.route_ids.filtered(lambda r: r.name.find('Deliver') >= 0)

    def test_00_sale_change_warehouse(self):
        so = self.so1

        so.action_confirm()
        self.assertTrue(so.state in ('sale', 'done'))
        self.assertTrue(so.picking_ids)
        org_picking = so.picking_ids
        self.assertEqual(org_picking.picking_type_id.warehouse_id, self.warehouse0)

        wiz = self.env['sale.line.change.order'].with_context(default_order_id=so.id).create({})
        self.assertTrue(wiz.line_ids)
        wiz.line_ids.line_warehouse_id = self.warehouse1
        wiz.line_ids.line_date_planned = '2018-01-01 00:00:00'
        wiz.apply()

        self.assertTrue(len(so.picking_ids) == 2)
        self.assertTrue(org_picking.state == 'cancel')
        new_picking = so.picking_ids - org_picking
        self.assertTrue(new_picking)
        self.assertEqual(new_picking.picking_type_id.warehouse_id, self.warehouse1)
        self.assertEqual(str(new_picking.scheduled_date), '2018-01-01 00:00:00')

    def test_01_sale_change_route(self):
        so = self.so1

        so.action_confirm()
        self.assertTrue(so.state in ('sale', 'done'))
        self.assertTrue(so.picking_ids)
        org_picking = so.picking_ids
        self.assertEqual(org_picking.picking_type_id.warehouse_id, self.warehouse0)

        # Change route on wizard line
        wiz = self.env['sale.line.change.order'].with_context(default_order_id=so.id).create({})
        self.assertTrue(wiz.line_ids)
        wiz.line_ids.line_route_id = self.dropship_route
        wiz.apply()

        # Check that RFQ/PO was created.
        self.assertTrue(org_picking.state == 'cancel')
        po_line = self.env['purchase.order.line'].search([('sale_line_id', '=', so.order_line.id)])
        self.assertTrue(po_line)

    def test_02_sale_dropshipping_to_warehouse(self):
        self.assertTrue(self.warehouse0_route)
        self.product1.route_ids += self.dropship_route
        so = self.so1

        so.action_confirm()
        self.assertTrue(so.state in ('sale', 'done'))
        self.assertFalse(so.picking_ids)

        # Change route on wizard line
        wiz = self.env['sale.line.change.order'].with_context(default_order_id=so.id).create({})
        self.assertTrue(wiz.line_ids)
        wiz.line_ids.line_route_id = self.warehouse0_route
        wiz.line_ids.line_date_planned = '2018-01-01 00:00:00'

        # Wizard cannot complete because of non-cancelled Purchase Order.
        with self.assertRaises(ValidationError):
            wiz.apply()

        po_line = self.env['purchase.order.line'].search([('sale_line_id', '=', so.order_line.id)])
        po_line.order_id.button_cancel()
        wiz.apply()

        # Check parameters on new picking
        self.assertTrue(so.picking_ids)
        self.assertEqual(so.picking_ids.picking_type_id.warehouse_id, self.warehouse0)
        self.assertEqual(str(so.picking_ids.scheduled_date), '2018-01-01 00:00:00')
