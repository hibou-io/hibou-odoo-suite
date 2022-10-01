# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields
from odoo.tests import common, Form


class TestTimesheetException(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.env = self.env(context=dict(self.env.context, tracking_disable=True))

    def test_timesheet_create_exception(self):
        exception = self.env.ref('timesheet_exception.except_unit_amount_over_eight_hours')
        exception.active = True
        project = self.env['project.project'].with_context(tracking_disable=True).create({
            'name': 'Project for selling timesheets',
        })
        today = fields.Date.today()
        service_category_id = self.env['product.category'].create({
            'name': 'Services',
            'parent_id': self.env.ref('product.product_category_1').id,
        }).id
        uom_hour_id = self.env.ref('uom.product_uom_hour').id
        product = self.env['product.product'].create({
            'name': 'Service Product (Prepaid Hours)',
            'categ_id': service_category_id,
            'type': 'service',
            'list_price': 250.00,
            'standard_price': 190.00,
            'invoice_policy': 'delivery',
            'uom_id': uom_hour_id,
            'uom_po_id': uom_hour_id,
            'default_code': 'SERV-DELI1',            
            'taxes_id': False,
        })
        product.product_tmpl_id.service_policy = 'ordered_timesheet'
        partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'company_id': False,
        })        
        so = self.env['sale.order'].with_context(mail_notrack=True, mail_create_nolog=True).create({
            'partner_id': partner.id,
            'project_id': project.id,
        })
        so_line = self.env['sale.order.line'].create([{
            'order_id': so.id,
            'name': product.name,
            'product_id': product.id,
            'product_uom_qty': 10,
            'qty_delivered': 2,
            'price_unit': product.list_price,
            'project_id': project.id,
        }])
        timesheet = self.env['account.analytic.line'].with_user(self.env.user).create({
            'name': "my timesheet 1",
            'project_id': project.id,            
            'date': today,
            'unit_amount': 9.0,
        })
        
        # Created exceptions on create.
        self.assertTrue(timesheet.exception_ids)
        
        # Will return action on write, which may or not be followed.
        action = timesheet.write({
            'name': 'Test Timesheet - Test Written',
        })
        self.assertTrue(timesheet.exception_ids)
        self.assertTrue(action)
        self.assertEqual(action.get('res_model'), 'timesheet.exception.confirm')

        # Simulation the opening of the wizard timesheet_exception_confirm and
        # set ignore_exception to True
        timesheet_exception_confirm = Form(self.env[action['res_model']].with_context(action['context'])).save()
        timesheet_exception_confirm.ignore = True
        timesheet_exception_confirm.action_confirm()
        self.assertTrue(timesheet.ignore_exception)
        
        # No exceptions should be on create with a lower than 8 in unit_amount
        # Also no exceptions because timesheet.so_line.product_template_id.service_policy == 'ordered_timesheet' and timesheet.so_line.qty_delivered + timesheet.unit_amount < timesheet.so_line.product_uom_qty
        timesheet = self.env['account.analytic.line'].with_user(self.env.user).create({
            'name': "my timesheet 1",
            'project_id': project.id,            
            'date': today,
            'unit_amount': 7.0,
        })
        self.assertFalse(timesheet.exception_ids)
        
        # timesheet.unit_amount = 17.0
        timesheet = self.env['account.analytic.line'].with_user(self.env.user).create({
            'name': "my timesheet 1",
            'project_id': project.id,            
            'date': today,
            'unit_amount': 17.0,
        })
        
        # Exceptions because timesheet.so_line.product_template_id.service_policy == 'ordered_timesheet' and timesheet.so_line.qty_delivered + timesheet.unit_amount > timesheet.so_line.product_uom_qty
        self.assertTrue(timesheet.exception_ids)
