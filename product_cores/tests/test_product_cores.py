# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo.tests import common, Form
from odoo import fields


class TestProductCores(common.TransactionCase):
    def setUp(self):
        super(TestProductCores, self).setUp()
        self.customer = self.env.ref('base.res_partner_2')
        self.vendor = self.env.ref('base.res_partner_12')
        self.purchase_tax_physical = self.env['account.tax'].create({
            'name': 'Purchase Tax Physical',
            'type_tax_use': 'purchase',
            'amount': 5.0,
        })
        self.purchase_tax_service = self.env['account.tax'].create({
            'name': 'Purchase Tax Service',
            'type_tax_use': 'purchase',
            'amount': 1.0,
        })
        self.sale_tax_physical = self.env['account.tax'].create({
            'name': 'Sale Tax Physical',
            'type_tax_use': 'sale',
            'amount': 5.0,
        })
        self.sale_tax_service = self.env['account.tax'].create({
            'name': 'Sale Tax Service',
            'type_tax_use': 'sale',
            'amount': 1.0,
        })
        self.product = self.env['product.product'].create({
            'name': 'Turbo',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_all').id,
            'supplier_taxes_id': [(6, 0, [self.purchase_tax_physical.id])],
            'taxes_id': [(6, 0, [self.sale_tax_physical.id])]
        })
        self.product_core_service = self.env['product.product'].create({
            'name': 'Turbo Core Deposit',
            'type': 'service',
            'categ_id': self.env.ref('product.product_category_all').id,
            'core_ok': True,
            'service_type': 'manual',
            'supplier_taxes_id': [(6, 0, [self.purchase_tax_service.id])],
            'taxes_id': [(6, 0, [self.sale_tax_service.id])]
        })
        self.product_core = self.env['product.product'].create({
            'name': 'Turbo Core',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_all').id,
            'core_ok': True,
        })
        self.product.product_core_id = self.product_core
        self.product.product_core_service_id = self.product_core_service

    def test_01_purchase(self):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
        })
        test_qty = 2.0
        po_line = self.env['purchase.order.line'].create({
            'order_id': purchase.id,
            'product_id': self.product.id,
            'name': 'Test',
            'date_planned': purchase.date_order,
            'product_qty': test_qty,
            'product_uom': self.product.uom_id.id,
            'price_unit': 10.0,
        })
        # Compute taxes since it didn't come from being created
        po_line._compute_tax_id()
        # No service line should have been created.
        self.assertEqual(len(purchase.order_line), 1)
        po_line.unlink()

        # Create a supplierinfo for this vendor with a core service product
        self.env['product.supplierinfo'].create({
            'name': self.vendor.id,
            'price': 10.0,
            'product_core_service_id': self.product_core_service.id,
            'product_tmpl_id': self.product.product_tmpl_id.id,
        })
        po_line = self.env['purchase.order.line'].create({
            'order_id': purchase.id,
            'product_id': self.product.id,
            'name': 'Test',
            'date_planned': purchase.date_order,
            'product_qty': test_qty,
            'product_uom': self.product.uom_id.id,
            'price_unit': 10.0,
        })
        po_line._compute_tax_id()
        # Ensure second line was created
        self.assertEqual(len(purchase.order_line), 2)
        # Ensure second line has the same quantity
        self.assertTrue(all(l.product_qty == test_qty for l in purchase.order_line))
        po_line_service = purchase.order_line.filtered(lambda l: l.product_id == self.product_core_service)
        self.assertTrue(po_line_service)
        # Ensure correct taxes
        self.assertEqual(po_line.taxes_id, self.purchase_tax_physical)
        self.assertEqual(po_line_service.taxes_id, self.purchase_tax_service)

        test_qty = 10.0
        po_line.product_qty = test_qty
        # Ensure second line has the same quantity
        self.assertTrue(all(l.product_qty == test_qty for l in purchase.order_line))

        purchase.button_confirm()
        self.assertEqual(purchase.state, 'purchase')
        self.assertEqual(len(purchase.picking_ids), 1)
        purchase.picking_ids.button_validate()

        # From purchase.tests.test_purchase_order_report in 13
        f = Form(self.env['account.move'].with_context(default_type='in_invoice'))
        f.partner_id = purchase.partner_id
        f.purchase_id = purchase
        vendor_bill = f.save()
        self.assertEqual(len(vendor_bill.invoice_line_ids), 2)
        vendor_bill.post()
        purchase.flush()

        # Duplicate PO
        # Should not 'duplicate' the original service line
        purchase2 = purchase.copy()
        self.assertEqual(len(purchase2.order_line), 2)
        po_line2 = purchase2.order_line.filtered(lambda l: l.product_id == self.product)
        po_line_service2 = purchase2.order_line.filtered(lambda l: l.product_id == self.product_core_service)
        self.assertTrue(po_line2)
        self.assertTrue(po_line_service2)
        # Should not be allowed to remove the service line.
        # Managers can remove the service line.
        # with self.assertRaises(UserError):
        #     po_line_service2.unlink()
        po_line2.unlink()
        # Deleting the main product line should delete the service line
        self.assertFalse(po_line2.exists())
        self.assertFalse(po_line_service2.exists())

    def test_02_sale(self):
        # Need Inventory.
        adjustment = self.env['stock.inventory'].create({
            'name': 'Initial',
            'product_ids': [(4, self.product.id)],
        })
        adjustment.action_start()
        if not adjustment.line_ids:
            adjustment_line = self.env['stock.inventory.line'].create({
                'inventory_id': adjustment.id,
                'product_id': self.product.id,
                'location_id': self.env.ref('stock.warehouse0').lot_stock_id.id,
            })
        adjustment.line_ids.write({
            # Maybe add Serial.
            'product_qty': 20.0,
        })
        adjustment.action_validate()

        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'date_order': fields.Datetime.now(),
            'picking_policy': 'direct',
        })
        test_qty = 2.0
        so_line = self.env['sale.order.line'].create({
            'order_id': sale.id,
            'product_id': self.product.id,
            'name': 'Test',
            'product_uom_qty': test_qty,
            'product_uom': self.product.uom_id.id,
            'price_unit': 10.0,
        })
        # Compute taxes since it didn't come from being created
        so_line._compute_tax_id()
        # Ensure second line was created
        self.assertEqual(len(sale.order_line), 2)
        # Ensure second line has the same quantity
        self.assertTrue(all(l.product_uom_qty == test_qty for l in sale.order_line))
        so_line_service = sale.order_line.filtered(lambda l: l.product_id == self.product_core_service)
        self.assertTrue(so_line_service)
        # Ensure correct taxes
        self.assertEqual(so_line.tax_id, self.sale_tax_physical)
        self.assertEqual(so_line_service.tax_id, self.sale_tax_service)

        test_qty = 1.0
        so_line.product_uom_qty = test_qty
        # Ensure second line has the same quantity
        self.assertTrue(all(l.product_qty == test_qty for l in sale.order_line))

        sale.action_confirm()
        self.assertTrue(sale.state in ('sale', 'done'))
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(len(sale.picking_ids.move_lines), 1)
        self.assertEqual(sale.picking_ids.move_lines.product_id, self.product)
        sale.picking_ids.action_assign()

        self.assertEqual(so_line.product_uom_qty, sale.picking_ids.move_lines.reserved_availability)
        res_dict = sale.picking_ids.button_validate()
        wizard = self.env[(res_dict.get('res_model'))].browse(res_dict.get('res_id'))
        wizard.process()
        self.assertEqual(so_line.qty_delivered, so_line.product_uom_qty)

        # Ensure all products are delivered.
        self.assertTrue(all(l.product_qty == l.qty_delivered for l in sale.order_line))

        # Duplicate SO
        # Should not 'duplicate' the original service line
        sale2 = sale.copy()
        self.assertEqual(len(sale2.order_line), 2)
        so_line2 = sale2.order_line.filtered(lambda l: l.product_id == self.product)
        so_line_service2 = sale2.order_line.filtered(lambda l: l.product_id == self.product_core_service)
        self.assertTrue(so_line2)
        self.assertTrue(so_line_service2)
        # Should not be allowed to remove the service line.
        # Managers can remove the service line
        # with self.assertRaises(UserError):
        #     so_line_service2.unlink()
        so_line2.unlink()
        # Deleting the main product line should delete the service line
        self.assertFalse(so_line2.exists())
        self.assertFalse(so_line_service2.exists())

        # Return the SO
        self.assertEqual(len(sale.picking_ids), 1)
        wiz = self.env['stock.return.picking'].with_context(active_model='stock.picking', active_id=sale.picking_ids.id).create({})
        wiz._onchange_picking_id()
        wiz.create_returns()
        self.assertEqual(len(sale.picking_ids), 2)

        return_picking = sale.picking_ids.filtered(lambda p: p.state != 'done')
        self.assertTrue(return_picking)
        res_dict = return_picking.button_validate()
        wizard = self.env[(res_dict.get('res_model'))].browse(res_dict.get('res_id'))
        wizard.process()

        self.assertTrue(all(l.qty_delivered == 0.0 for l in sale.order_line))
