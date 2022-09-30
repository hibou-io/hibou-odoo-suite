# from odoo.tests import common
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
# from odoo.tests.common import Form


@tagged('post_install', '-at_install')
class TestAccountMoveException(AccountTestInvoicingCommon):

    def test_10_validation_on_post(self):
        self.env.user.groups_id += self.env.ref('analytic.group_analytic_accounting')
        exception = self.env.ref('account_exception.except_no_phone').sudo()
        exception.active = True
        invoice = self.init_invoice('out_invoice', products=self.product_a)

        # must be exceptions when no phone and posting
        invoice.partner_id.phone = False
        invoice.action_post()
        self.assertTrue(invoice.exception_ids)

        # no exceptions when phone and posting
        invoice.partner_id.phone = '123'
        invoice.action_post()
        self.assertFalse(invoice.exception_ids)
