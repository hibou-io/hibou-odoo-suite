from odoo import fields
from odoo.tests import common
from datetime import datetime, timedelta


class TestPurchaseBySaleHistory(common.TransactionCase):

    def test_00_wizard(self):
        wh1 = self.env.ref('stock.warehouse0')
        wh2 = self.env['stock.warehouse'].create({
            'name': 'WH2',
            'code': 'twh2',
        })

        sale_partner = self.env.ref('base.res_partner_2')
        purchase_partner = self.env['res.partner'].create({
            'name': 'Purchase Partner',
        })

        product11 = self.env['product.product'].create({
            'name': 'Product 1',
            'type': 'product',
        })
        product12 = self.env['product.product'].create({
            'name': 'Product 1.1',
            'type': 'product',
            'product_tmpl_id': product11.product_tmpl_id.id,
        })
        product2 = self.env['product.product'].create({
            'name': 'Product 2',
            'type': 'product',
        })

        po1 = self.env['purchase.order'].create({
            'partner_id': purchase_partner.id,
        })

        # Create initial wizard, it won't apply to any products because the PO is empty, and the vendor
        # doesn't supply any products yet.
        wiz = self.env['purchase.sale.history.make'].create({
            'purchase_id': po1.id,
        })

        self.assertEqual(wiz.product_count, 0.0, 'There shouldn\'t be any products for this vendor yet.')

        # Assign vendor to products created earlier.
        self.env['product.supplierinfo'].create({
            'name': purchase_partner.id,
            'product_tmpl_id': product11.product_tmpl_id.id,
            'product_id': product11.id,
        })
        self.env['product.supplierinfo'].create({
            'name': purchase_partner.id,
            'product_tmpl_id': product2.product_tmpl_id.id,
        })
        # New wizard picks up the correct number of products supplied by this vendor.
        wiz = self.env['purchase.sale.history.make'].create({
            'purchase_id': po1.id,
        })
        self.assertEqual(wiz.product_count, 2)

        # Make some sales history...
        sale_date = fields.Datetime.to_string(datetime.now() - timedelta(days=30))
        self.env['sale.order'].create({
            'partner_id': sale_partner.id,
            'date_order': sale_date,
            'confirmation_date': sale_date,
            'picking_policy': 'direct',
            'order_line': [
                (0, 0, {'product_id': product11.id, 'product_uom_qty': 3.0}),
                (0, 0, {'product_id': product12.id, 'product_uom_qty': 3.0}),
                (0, 0, {'product_id': product2.id, 'product_uom_qty': 3.0}),
            ],
        }).action_confirm()

        days = 60
        history_start = fields.Date.to_string(datetime.now() - timedelta(days=days))
        history_end = fields.Date.today()
        wiz.write({
            'history_start': history_start,
            'history_end': history_end,
            'procure_days': days,
            'history_warehouse_ids': [(4, wh1.id, None)],
        })
        self.assertEqual(wiz.history_days, days)
        wiz.action_confirm()
        self.assertEqual(po1.order_line.filtered(lambda l: l.product_id == product11).product_qty, 3.0 + 3.0)  # 3 from Sales History, 3 from Demand (from the sale)
        self.assertEqual(po1.order_line.filtered(lambda l: l.product_id == product12).product_qty, 0.0)
        self.assertEqual(po1.order_line.filtered(lambda l: l.product_id == product2).product_qty, 3.0 + 3.0)

        # Make additional sales history...
        sale_date = fields.Datetime.to_string(datetime.now() - timedelta(days=15))
        self.env['sale.order'].create({
            'partner_id': sale_partner.id,
            'date_order': sale_date,
            'confirmation_date': sale_date,
            'picking_policy': 'direct',
            'order_line': [
                (0, 0, {'product_id': product11.id, 'product_uom_qty': 3.0}),
                (0, 0, {'product_id': product12.id, 'product_uom_qty': 3.0}),
                (0, 0, {'product_id': product2.id, 'product_uom_qty': 3.0}),
            ],
        }).action_confirm()

        wiz.action_confirm()
        self.assertEqual(po1.order_line.filtered(lambda l: l.product_id == product11).product_qty, 6.0 + 6.0)
        self.assertEqual(po1.order_line.filtered(lambda l: l.product_id == product12).product_qty, 0.0)
        self.assertEqual(po1.order_line.filtered(lambda l: l.product_id == product2).product_qty, 6.0 + 6.0)

        # Make additional sales history in other warehouse
        sale_date = fields.Datetime.to_string(datetime.now() - timedelta(days=15))
        self.env['sale.order'].create({
            'partner_id': sale_partner.id,
            'date_order': sale_date,
            'confirmation_date': sale_date,
            'picking_policy': 'direct',
            'warehouse_id': wh2.id,
            'order_line': [
                (0, 0, {'product_id': product11.id, 'product_uom_qty': 3.0}),
                (0, 0, {'product_id': product12.id, 'product_uom_qty': 3.0}),
                (0, 0, {'product_id': product2.id, 'product_uom_qty': 3.0}),
            ],
        }).action_confirm()

        wiz.action_confirm()
        self.assertEqual(po1.order_line.filtered(lambda l: l.product_id == product11).product_qty, 6.0 + 6.0)
        self.assertEqual(po1.order_line.filtered(lambda l: l.product_id == product12).product_qty, 0.0)
        self.assertEqual(po1.order_line.filtered(lambda l: l.product_id == product2).product_qty, 6.0 + 6.0)

        # Make additional sales history that should NOT be counted...
        sale_date = fields.Datetime.to_string(datetime.now() - timedelta(days=61))
        self.env['sale.order'].create({
            'partner_id': sale_partner.id,
            'date_order': sale_date,
            'confirmation_date': sale_date,
            'picking_policy': 'direct',
            'order_line': [
                (0, 0, {'product_id': product11.id, 'product_uom_qty': 3.0}),
                (0, 0, {'product_id': product12.id, 'product_uom_qty': 3.0}),
                (0, 0, {'product_id': product2.id, 'product_uom_qty': 3.0}),
            ],
        }).action_confirm()

        wiz.action_confirm()
        self.assertEqual(po1.order_line.filtered(lambda l: l.product_id == product11).product_qty, 6.0 + 9.0)
        self.assertEqual(po1.order_line.filtered(lambda l: l.product_id == product12).product_qty, 0.0)
        self.assertEqual(po1.order_line.filtered(lambda l: l.product_id == product2).product_qty, 6.0 + 9.0)

        # Test that the wizard will only use the existing PO line products now that we have lines.
        po1.order_line.filtered(lambda l: l.product_id == product2).unlink()
        wiz.action_confirm()
        self.assertEqual(po1.order_line.filtered(lambda l: l.product_id == product11).product_qty, 6.0 + 9.0)
        self.assertEqual(po1.order_line.filtered(lambda l: l.product_id == product12).product_qty, 0.0)
        self.assertEqual(po1.order_line.filtered(lambda l: l.product_id == product2).product_qty, 0.0)

        # Plan for 1/2 the days of inventory
        wiz.procure_days = days / 2.0
        wiz.action_confirm()
        self.assertEqual(po1.order_line.filtered(lambda l: l.product_id == product11).product_qty, 3.0 + 9.0)

        # Cause Inventory on existing product to make sure we don't order it.
        adjust_product11 = self.env['stock.inventory'].create({
            'name': 'Product11',
            'location_id': wh1.lot_stock_id.id,
            'product_id': product11.id,
            'filter': 'product',
        })
        adjust_product11.action_start()
        adjust_product11.line_ids.create({
            'inventory_id': adjust_product11.id,
            'product_id': product11.id,
            'product_qty': 100.0,
            'location_id': wh1.lot_stock_id.id,
        })
        adjust_product11.action_validate()

        wiz.action_confirm()
        self.assertEqual(po1.order_line.filtered(lambda l: l.product_id == product11).product_qty, 0.0)  # Because we have so much in stock now.
        self.assertEqual(po1.order_line.filtered(lambda l: l.product_id == product12).product_qty, 0.0)
        self.assertEqual(po1.order_line.filtered(lambda l: l.product_id == product2).product_qty, 0.0)
