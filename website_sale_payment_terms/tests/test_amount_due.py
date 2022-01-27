from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestWebsiteSalePaymentTerms(TransactionCase):
    def setUp(self):
        super(TestWebsiteSalePaymentTerms, self).setUp()
        self.env.company.currency_id = self.browse_ref('base.USD')
        self.so = self.env['sale.order'].create({
            'partner_id': self.ref('base.res_partner_12'),
            'order_line': [(0, 0, {
                'product_id': self.env['product.product'].create({'name': 'Product A', 'list_price': 100}).id,
                'product_uom_qty': 1,
                'name': 'Product A',
                'tax_id': False,
            })]
        })

    def test_00_immediate(self):
        # Double-check that we're asking for money if no payment terms are set
        self.assertEqual(self.so.amount_due_today, self.so.amount_total)

        immediate_terms = self.browse_ref('account.account_payment_term_immediate')
        self.so._check_payment_term_quotation(immediate_terms.id)
        self.assertEqual(self.so.amount_due_today, self.so.amount_total)

    def test_10_thirty_percent(self):
        thirty_percent_terms = self.browse_ref('account.account_payment_term_advance_60days')
        self.so._check_payment_term_quotation(thirty_percent_terms.id)
        self.assertEqual(self.so.amount_due_today, 30.0)

    def test_20_fifteen_days(self):
        fifteen_days_terms = self.browse_ref('account.account_payment_term_15days')
        self.so._check_payment_term_quotation(fifteen_days_terms.id)
        self.assertEqual(self.so.amount_due_today, 0.0)

    def test_30_deposit_requested(self):
        """
        Ask for deposit if deposit amount is greater
        """
        thirty_percent_terms = self.browse_ref('account.account_payment_term_advance_60days')
        thirty_percent_terms.deposit_percentage = 40
        thirty_percent_terms.deposit_flat = 5
        self.so._check_payment_term_quotation(thirty_percent_terms.id)
        self.assertEqual(self.so.amount_due_today, 45.0)

    def test_40_low_deposit(self):
        """
        Ask for terms amount if greater than requested deposit
        """
        thirty_percent_terms = self.browse_ref('account.account_payment_term_advance_60days')
        thirty_percent_terms.deposit_percentage = 20
        thirty_percent_terms.deposit_flat = 5
        self.so._check_payment_term_quotation(thirty_percent_terms.id)
        self.assertEqual(self.so.amount_due_today, 30.0)
