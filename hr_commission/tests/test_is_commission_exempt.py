from odoo.tests import common
import logging


_logger = logging.getLogger(__name__)


class TestIsCommissionExempt(common.TransactionCase):
    def setUp(self):
        super().setUp()

        # find and configure company commissions journal
        expense_user_type = self.env['account.account.type'].search([('name', '=', 'Expenses')], limit=1)
        self.assertTrue(expense_user_type)
        expense_account = self.env['account.account'].search([('user_type_id', '=', expense_user_type.id),
                                                              ('company_id', '=', self.env.user.company_id.id)], limit=1)
        self.assertTrue(expense_account)
        commission_journal = self.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', expense_account.company_id.id),
        ], limit=1)
        self.assertTrue(commission_journal)
        commission_journal.default_account_id = expense_account
        commission_journal.default_account_id = expense_account
        self.env.user.company_id.commission_journal_id = commission_journal
        self.env.user.company_id.commission_type = 'on_invoice'

        self.sales_user = self.browse_ref('base.user_demo')
        self.customer_partner = self.browse_ref('base.res_partner_12')

        self.sales_employee = self.sales_user.employee_id
        self.sales_employee.write({
            'address_home_id': self.sales_user.partner_id,
            'contract_ids': [(0, 0, {
                'date_start': '2016-01-01',
                'date_end': '2030-12-31',
                'name': 'Contract for tests',
                'wage': 1000.0,
                # 'type_id': self.ref('hr_contract.hr_contract_type_emp'),
                'employee_id': self.sales_employee.id,
                'resource_calendar_id': self.ref('resource.resource_calendar_std'),
                'commission_rate': 10.0,
                'state': 'open',  # if not "Running" then no automatic selection when Payslip is created in 11.0
            })],
        })

        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'invoice_policy': 'order',
            'taxes_id': [],
        })
        self.product_is_commission_exempt = self.env['product.product'].create({
            'name': 'Test Product No Commission',
            'invoice_policy': 'order',
            'is_commission_exempt': True,
            'taxes_id': [],
        })

    def _createSaleOrder(self):
        order = self.env['sale.order'].create({
            'partner_id': self.customer_partner.id,
            'user_id': self.sales_user.id,
            'order_line': [(0, 0, {
                'name': 'test product',
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'product_uom': self.product.uom_id.id,
                'price_unit': 100.0,
                'tax_id': False,
            }), (0, 0, {
                'name': 'test product no commission',
                'product_id': self.product_is_commission_exempt.id,
                'product_uom_qty': 1.0,
                'product_uom': self.product_is_commission_exempt.uom_id.id,
                'price_unit': 20.0,
                'tax_id': False,
            })]
        })
        self.assertEqual(order.amount_total, 120.0)
        return order

    def test_00_is_commission_exempt_total(self):
        # TODO: test refunds

        # New attribute
        self.assertFalse(self.product.is_commission_exempt)
        self.assertTrue(self.product_is_commission_exempt.is_commission_exempt)

        # Calculate commission based on invoice total
        self.env.user.company_id.commission_amount_type = 'on_invoice_total'

        sale = self._createSaleOrder()
        sale.action_confirm()
        self.assertIn(sale.state, ('sale', 'done'), 'Could not confirm, maybe archive exception rules.')
        inv = sale._create_invoices()
        self.assertFalse(inv.commission_ids, 'Commissions exist when invoice is created.')
        inv.action_post()
        self.assertTrue(inv.commission_ids, 'Commissions not created when invoice is validated.')
        self.assertEqual(inv.amount_total, 120.0)

        user_commission = inv.commission_ids.filtered(lambda c: c.employee_id.id == self.sales_employee.id)
        self.assertEqual(len(user_commission), 1)

        # rate = 10.0, total = 120.0, commission total = 100.0
        # commmission should be 10.0
        self.assertEqual(user_commission.amount, 10.0)

    def test_10_is_commission_exempt_margin(self):
        self.env['ir.config_parameter'].set_param('commission.margin.threshold', '51.0')
        low_margin_product = self.env['product.product'].create({
            'name': 'Test Low Margin Product',
            'standard_price': 100.0,
            'invoice_policy': 'order',
        })
        self.env.user.company_id.commission_amount_type = 'on_invoice_margin'
        self.product.standard_price = 50.0 # margin is 100%, margin = $50.0
        self.product_is_commission_exempt.standard_price = 10.0 # margin is 100%

        sale = self._createSaleOrder()
        sale.write({
            'order_line': [(0, 0, {
                'name': 'test low margin product',
                'product_id': low_margin_product.id,
                'product_uom_qty': 1.0,
                'product_uom': low_margin_product.uom_id.id,
                'price_unit': 101.0, # margin is 1.0 %
                'tax_id': False,
            })],
        })

        # Total margin is now $61.0, but eligible margin should still be $50.0
        sale.action_confirm()
        self.assertIn(sale.state, ('sale', 'done'), 'Could not confirm, maybe archive exception rules.')
        inv = sale._create_invoices()
        self.assertEqual(inv.invoice_line_ids.mapped(lambda l: l.get_margin_percent()), [100.0, 100.0, 1.0])
        self.assertFalse(inv.commission_ids, 'Commissions exist when invoice is created.')
        inv.action_post()
        self.assertTrue(inv.commission_ids, 'Commissions not created when invoice is validated.')

        user_commission = inv.commission_ids.filtered(lambda c: c.employee_id.id == self.sales_employee.id)
        self.assertEqual(len(user_commission), 1)

        # rate = 10.0, total margin = 60.0, commission margin = 50.0
        # commission should be 5.0
        self.assertEqual(user_commission.amount, 5.0)

    def test_20_test_zero_price(self):
        self.env.user.company_id.commission_amount_type = 'on_invoice_margin'
        self.product.standard_price = 0.0  # margin_percent is NaN
        self.product_is_commission_exempt.standard_price = 10.0  # margin is 100%

        sale = self._createSaleOrder()
        sale.action_confirm()
        self.assertIn(sale.state, ('sale', 'done'), 'Could not confirm, maybe archive exception rules.')
        inv = sale._create_invoices()
        self.assertEqual(inv.invoice_line_ids.mapped(lambda l: l.get_margin_percent()), [-1.0, 100.0])
