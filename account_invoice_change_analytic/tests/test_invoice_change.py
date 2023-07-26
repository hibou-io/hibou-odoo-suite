from odoo.tests import tagged, Form
from odoo.addons.account_invoice_change.tests.test_invoice_change import InvoiceChangeCommon


@tagged('post_install', '-at_install')
class TestWizard(InvoiceChangeCommon):
    def setUp(self):
        super().setUp()
        self.analytic_account = self.env['account.analytic.account'].create({
            'name': 'test account',
        })
        self.analytic_account2 = self.env['account.analytic.account'].create({
            'name': 'test account2',
        })
        self.analytic_account3 = self.env['account.analytic.account'].create({
            'name': 'test account3',
        })
        self.analytic_tag1 = self.env['account.analytic.tag'].create({
            'name': 'Tag 1',
            'active_analytic_distribution': True,
            'analytic_distribution_ids': [
                (0, 0, {'account_id': self.analytic_account.id, 'percentage': 30.0}),
                (0, 0, {'account_id': self.analytic_account2.id, 'percentage': 70.0}),
            ],
        })
        self.analytic_tag2 = self.env['account.analytic.tag'].create({
            'name': 'Tag 2',
            'active_analytic_distribution': True,
            'analytic_distribution_ids': [
                (0, 0, {'account_id': self.analytic_account.id, 'percentage': 60.0}),
                (0, 0, {'account_id': self.analytic_account3.id, 'percentage': 40.0}),
            ],
        })
    
    def test_invoice_change_analytic_account(self):
        self.assertEqual(self.invoice_basic.state, 'draft')
        self.invoice_basic.action_post()
        self.assertEqual(self.invoice_basic.state, 'posted')
        
        # Tests Adding an Analytic Account
        self.assertFalse(self.invoice_basic.line_ids.mapped('analytic_account_id'))
        ctx = {'active_model': 'account.move', 'active_ids': [self.invoice_basic.id]}
        change = Form(self.env['account.invoice.change'].with_context(ctx))
        change.analytic_account_id = self.analytic_account
        change.save().affect_change()
        # Do not want to set analytic account on receivable lines
        invoice_lines = self.invoice_basic.invoice_line_ids
        other_lines = self.invoice_basic.line_ids - invoice_lines
        self.assertEqual(invoice_lines.analytic_account_id, self.analytic_account)
        self.assertFalse(other_lines.analytic_account_id)
        self.assertEqual(invoice_lines.analytic_line_ids.account_id, self.analytic_account)
        
        # Tests Changing Analytic Account
        ctx = {'active_model': 'account.move', 'active_ids': [self.invoice_basic.id]}
        change = Form(self.env['account.invoice.change'].with_context(ctx))
        change.analytic_account_id = self.analytic_account2
        change.save().affect_change()
        self.assertEqual(invoice_lines.analytic_account_id, self.analytic_account2)
        self.assertFalse(other_lines.analytic_account_id)
        self.assertEqual(invoice_lines.analytic_line_ids.account_id, self.analytic_account2)

        # Tests Removing Analytic Account
        ctx = {'active_model': 'account.move', 'active_ids': [self.invoice_basic.id]}
        change = Form(self.env['account.invoice.change'].with_context(ctx))
        change.analytic_account_id = self.env['account.analytic.account']
        change.save().affect_change()
        self.assertFalse(invoice_lines.analytic_account_id)
        self.assertFalse(other_lines.analytic_account_id)
        self.assertFalse(invoice_lines.analytic_line_ids)

        
    
    def test_invoice_change_analytic_tags(self):
        invoice_lines = self.invoice_basic.invoice_line_ids
        other_lines = self.invoice_basic.line_ids - invoice_lines
        
        self.assertEqual(self.invoice_basic.state, 'draft')
        invoice_lines.analytic_tag_ids = self.analytic_tag1
        self.invoice_basic.action_post()
        self.assertEqual(self.invoice_basic.state, 'posted')
        
        self.assertEqual(invoice_lines.analytic_line_ids.mapped(lambda l: (l.account_id, l.amount)), 
                         [(self.analytic_account, 300.0),
                          (self.analytic_account2, 700.0)])
        
        # Tests Adding an Analytic Account Tag
        self.assertFalse(self.invoice_basic.line_ids.mapped('analytic_account_id'))
        ctx = {'active_model': 'account.move', 'active_ids': [self.invoice_basic.id]}
        change = Form(self.env['account.invoice.change'].with_context(ctx))
        change.update_tags = 'add'
        change.analytic_tag_ids.add(self.analytic_tag2)
        change.save().affect_change()
        
        self.assertEqual(invoice_lines.analytic_tag_ids, self.analytic_tag1 | self.analytic_tag2)
        self.assertFalse(other_lines.analytic_tag_ids)
        self.assertEqual(invoice_lines.analytic_line_ids.mapped(lambda l: (l.account_id, l.amount)), 
                         [(self.analytic_account, 300.0),
                          (self.analytic_account2, 700.0),
                          (self.analytic_account, 600.0),
                          (self.analytic_account3, 400.0)])
        
        # Tests Replacing all Analytic Account Tags
        self.assertFalse(self.invoice_basic.line_ids.mapped('analytic_account_id'))
        ctx = {'active_model': 'account.move', 'active_ids': [self.invoice_basic.id]}
        change = Form(self.env['account.invoice.change'].with_context(ctx))
        self.assertEqual(change.analytic_tag_ids[:], self.analytic_tag1 | self.analytic_tag2)
        change.update_tags = 'set'
        change.analytic_tag_ids.clear()
        change.analytic_tag_ids.add(self.analytic_tag2)
        change.save().affect_change()
        
        self.assertEqual(invoice_lines.analytic_tag_ids, self.analytic_tag2)
        self.assertFalse(other_lines.analytic_tag_ids)
        self.assertEqual(invoice_lines.analytic_line_ids.mapped(lambda l: (l.account_id, l.amount)), 
                         [(self.analytic_account, 600.0),
                          (self.analytic_account3, 400.0)])
