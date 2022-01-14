# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields
from odoo.tests import common, Form
from odoo.addons.base_exception.tests.purchase_test import PurchaseTest, LineTest
# from odoo.addons.base_exception.tests.test_base_exception import TestBaseException

from .common import setup_test_model
from .purchase_test import PurchaseUserTest, PurchaseTestExceptionRuleConfirm
import logging
_logger = logging.getLogger(__name__)


@common.tagged("post_install", "-at_install")
class TestBaseExceptionUser(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestBaseExceptionUser, cls).setUpClass()
        setup_test_model(cls.env, [PurchaseTest, PurchaseUserTest, LineTest, PurchaseTestExceptionRuleConfirm])

        group_id = cls.env.ref('base_exception_user.group_exception_rule_user').id
        user_dict = {
            "name": "User test",
            "login": "tua@example.com",
            "password": "base-test-passwd",
            "email": "armande.hruser@example.com",
            "groups_id": [(6, 0, [group_id])],
        }
        cls.user_test = cls.env['res.users'].create(user_dict)

        cls.env['ir.model.access'].create([
            {'name': 'Test PO Access',
             'model_id': cls.env['ir.model'].search([('model', '=', 'base.exception.test.purchase')]).id,
             'group_id': group_id,
             'perm_read': True,
             'perm_write': True,
             'perm_create': True,
             'perm_unlink': True,
             },
            {'name': 'Test PO Line Access',
             'model_id': cls.env['ir.model'].search([('model', '=', 'base.exception.test.purchase.line')]).id,
             'group_id': group_id,
             'perm_read': True,
             'perm_write': True,
             'perm_create': True,
             'perm_unlink': True,
             },
            {'name': 'Test PO Wizard Access',
             'model_id': cls.env['ir.model'].search([('model', '=', 'purchase.test.exception.rule.confirm')]).id,
             'group_id': group_id,
             'perm_read': True,
             'perm_write': True,
             'perm_create': True,
             'perm_unlink': True,
             },
        ])


        cls.base_exception = cls.env["base.exception"]
        cls.exception_rule = cls.env["exception.rule"]
        if "test_purchase_ids" not in cls.exception_rule._fields:
            field = fields.Many2many("base.exception.test.purchase")
            cls.exception_rule._add_field("test_purchase_ids", field)
            cls.exception_rule._fields["test_purchase_ids"].depends_context = None
        cls.exception_confirm = cls.env["exception.rule.confirm"]
        cls.exception_rule._fields["model"].selection.append(
            ("base.exception.test.purchase", "Purchase Order")
        )

        cls.exception_rule._fields["model"].selection.append(
            ("base.exception.test.purchase.line", "Purchase Order Line")
        )

        cls.exceptionnozip = cls.env["exception.rule"].create(
            {
                "name": "No ZIP code on destination",
                "sequence": 10,
                "model": "base.exception.test.purchase",
                "code": "if not self.partner_id.zip: failed=True",
                "allow_user_ignore": False,
            }
        )

        cls.exceptionno_minorder = cls.env["exception.rule"].create(
            {
                "name": "Min order except",
                "sequence": 10,
                "model": "base.exception.test.purchase",
                "code": "if self.amount_total <= 200.0: failed=True",
                "allow_user_ignore": False,
            }
        )

        cls.exceptionno_lineqty = cls.env["exception.rule"].create(
            {
                "name": "Qty > 0",
                "sequence": 10,
                "model": "base.exception.test.purchase.line",
                "code": "if obj.qty <= 0: failed=True",
                "allow_user_ignore": False,
            }
        )

    def test_purchase_order_exception_ignore(self):
        # _logger.warning('starting test_purchase_order_exception_ignore')
        partner = self.env.ref("base.res_partner_1")
        partner.zip = False
        potest1 = self.env['base.exception.test.purchase'].with_user(self.user_test).create(
            {
                "name": "Test base exception to basic purchase",
                "partner_id": partner.id,
                "line_ids": [
                    (0, 0, {"name": "line test", "amount": 120.0, "qty": 1.5})
                ],
            }
        )
        # Block because of exception during validation: return exception wizard
        action = potest1.button_confirm()
        self.assertEqual(action.get('res_model'), 'purchase.test.exception.rule.confirm')
        wizard = Form(self.env[action['res_model']].with_context(action['context'])).save()
        self.assertFalse(wizard.show_ignore_button)
        self.assertFalse(wizard.action_ignore())

        self.exceptionnozip.allow_user_ignore = True
        self.exceptionno_minorder.allow_user_ignore = True
        self.exceptionno_lineqty.allow_user_ignore = True

        action = potest1.button_confirm()
        wizard = Form(self.env[action['res_model']].with_user(self.user_test).with_context(action['context'])).save()
        self.assertTrue(wizard.show_ignore_button)
        action = wizard.action_ignore()
        self.assertEqual(action.get('type'), 'ir.actions.act_window_close')
