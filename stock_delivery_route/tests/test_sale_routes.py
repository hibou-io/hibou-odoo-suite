from odoo.tests import common


class TestSaleRoutes(common.TransactionCase):

    def test_plan_two_warehouses(self):
        partner = self.env.ref('base.res_partner_2')
        product_1 = self.env.ref('product.product_product_24_product_template')
        wh_1 = self.env.ref('stock.stock_warehouse_shop0')
        delivery_route = self.env['stock.warehouse.delivery.route'].create({
            'name': 'Test',
            'warehouse_id': wh_1.id,
        })
        so = self.env['sale.order'].create({
            'warehouse_id': wh_1.id,
            'partner_id': partner.id,
            'order_line': [(0, 0, {'product_id': product_1.product_variant_id.id})],
            'delivery_route_id': delivery_route.id,
        })
        so.action_confirm()
        self.assertTrue(so.state in ('sale', 'done'))
        self.assertEqual(so.picking_ids[0].delivery_route_id, delivery_route)
