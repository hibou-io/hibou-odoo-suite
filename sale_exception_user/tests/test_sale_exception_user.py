# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo.tests import Form, TransactionCase


class TestSaleException(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        groups = (cls.env.ref('base_exception_user.group_exception_rule_user') |
                  cls.env.ref('sales_team.group_sale_manager'))
        user_dict = {
            "name": "User test",
            "login": "tua@example.com",
            "password": "base-test-passwd",
            "email": "armande.hruser@example.com",
            "groups_id": [(6, 0, groups.ids)],
        }
        cls.user_test = cls.env['res.users'].create(user_dict)
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

    def test_sale_exception_user(self):
        with self.with_user(self.user_test.login):
            exception = self.env.ref("sale_exception.excep_no_zip").sudo()
            exception.active = True
            exception.allow_user_ignore = True

            partner = self.env.ref("base.res_partner_1")
            partner.zip = False
            p = self.env.ref("product.product_product_6")
            so1 = self.env["sale.order"].create(
                {
                    "partner_id": partner.id,
                    "partner_invoice_id": partner.id,
                    "partner_shipping_id": partner.id,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "name": p.name,
                                "product_id": p.id,
                                "product_uom_qty": 2,
                                "product_uom": p.uom_id.id,
                                "price_unit": p.list_price,
                            },
                        )
                    ],
                    "pricelist_id": self.env.ref("product.list0").id,
                }
            )

            action = so1.action_confirm()
            wizard = Form(self.env[action['res_model']].with_user(self.user_test).with_context(action['context'])).save()
            self.assertTrue(wizard.show_ignore_button)
            action = wizard.action_ignore()
            self.assertEqual(action.get('type'), 'ir.actions.act_window_close')
            self.assertTrue(so1.ignore_exception)
            self.assertEqual(so1.state, 'sale')
