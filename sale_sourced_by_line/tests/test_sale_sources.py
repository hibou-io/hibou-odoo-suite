from odoo.tests import common


class TestSaleSources(common.TransactionCase):

    def test_plan_two_warehouses(self):
        partner = self.env.ref('base.res_partner_2')
        product_1 = self.env.ref('product.product_product_24_product_template')
        product_2 = self.env.ref('product.product_product_16_product_template')
        wh_1 = self.env.ref('stock.stock_warehouse_shop0')
        wh_2 = self.env.ref('stock.warehouse0')
        so = self.env['sale.order'].create({
            'warehouse_id': wh_1.id,
            'partner_id': partner.id,
            'date_planned': '2018-01-01',
            'order_line': [(0, 0, {'product_id': product_1.product_variant_id.id}),
                           (0, 0, {'product_id': product_2.product_variant_id.id, 'date_planned': '2018-02-01', 'warehouse_id': wh_2.id})]
        })
        so.action_confirm()
        self.assertTrue(so.state in ('sale', 'done'))
        self.assertEqual(len(so.picking_ids), 2)
        self.assertEqual(len(so.picking_ids.filtered(lambda p: p.picking_type_id.warehouse_id == wh_1)), 1)
        self.assertEqual(len(so.picking_ids.filtered(lambda p: p.picking_type_id.warehouse_id == wh_2)), 1)
