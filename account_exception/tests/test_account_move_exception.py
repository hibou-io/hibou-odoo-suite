from odoo.tests import Form
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestAccountMoveException(AccountTestInvoicingCommon):

    def test_10_validation_on_post(self):
        self.env.user.groups_id += self.env.ref('analytic.group_analytic_accounting')
        exception = self.env.ref('account_exception.except_no_phone').sudo()
        exception.active = True
        invoice = self.init_invoice('out_invoice', products=self.product_a)

        # must be exceptions when no phone and posting
        invoice.partner_id.phone = False
        action = invoice.action_post()
        self.assertTrue(invoice.exception_ids)
        self.assertEqual(invoice.state, 'draft')

        wizard_model = action.get('res_model', '')
        self.assertEqual(wizard_model, 'account.move.exception.confirm')
        wizard = Form(self.env[wizard_model].with_context(action['context'])).save()
        self.assertFalse(wizard.show_ignore_button)

        # no exceptions when ignoring exceptions and posting
        invoice.ignore_exception = True
        invoice.action_post()
        self.assertFalse(invoice.exception_ids)
        self.assertEqual(invoice.state, 'posted')

        # no exceptions when phone and posting
        invoice.button_draft()
        invoice.ignore_exception = False
        invoice.partner_id.phone = '123'
        invoice.action_post()
        self.assertFalse(invoice.exception_ids)
        self.assertEqual(invoice.state, 'posted')
