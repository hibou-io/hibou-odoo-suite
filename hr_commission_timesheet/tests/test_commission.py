# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo.tests import common


class TestCommission(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.sales_user = self._createUser()
        self.sales_employee = self._createEmployee(self.sales_user)
        self.user = self.env.ref('base.user_demo')
        self.employee = self.env.ref('hr.employee_qdp')  # This is the employee associated with above user.
        self.employee_contract = self._createContract(self.employee, 0.0, 0.0, 5.0)
        self.product = self.env.ref('product.product_product_1')
        self.product.write({
            'lst_price': 100.0,
            'type': 'service',
            'service_policy': 'delivered_timesheet',
            'service_tracking': 'task_in_project',
        })
        self.partner = self.env.ref('base.res_partner_2')

    def _createUser(self, login='coach'):
        return self.env['res.users'].create({
            'name': 'Coach',
            'email': 'coach',
            'login': login,
        })

    def _createEmployee(self, user):
        return self.env['hr.employee'].create({
            'birthday': '1985-03-14',
            'country_id': self.ref('base.us'),
            'department_id': self.ref('hr.dep_rd'),
            'gender': 'male',
            'name': 'Jared',
            'address_home_id': user.partner_id.id,
            'user_id': user.id,
        })

    def _createContract(self, employee, commission_rate, admin_commission_rate=0.0, timesheet_rate=0.0):
        return self.env['hr.contract'].create({
            'date_start': '2016-01-01',
            'date_end': '2030-12-31',
            'name': 'Contract for tests',
            'wage': 1000.0,
            # 'type_id': self.ref('hr_contract.hr_contract_type_emp'),
            'employee_id': employee.id,
            'resource_calendar_id': self.ref('resource.resource_calendar_std'),
            'commission_rate': commission_rate,
            'admin_commission_rate': admin_commission_rate,
            'timesheet_commission_rate': timesheet_rate,
            'state': 'open',  # if not "Running" then no automatic selection when Payslip is created in 11.0
        })

    def _create_sale(self, user):
        # Create sale
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 150.0,
                }),
            ],
            'user_id': user.id,
        })

        self.assertEqual(sale.user_id.id, user.id)
        self.assertEqual(sale.state, 'draft')
        return sale

    def test_01_workflow(self):
        sale = self._create_sale(self.sales_user)
        self.assertEqual(sale.amount_total, 250.0, "Order total not correct (maybe taxed?).")
        self.assertEqual(sale.user_id, self.sales_user, "Salesperson not correct.")
        sale.action_confirm()

        self.assertIn(sale.state, ('sale', 'done'))
        self.assertEqual(sale.invoice_status, 'no', "SO should be invoiced on timesheets.")
        self.assertEqual(len(sale.tasks_ids), 2)
        task_1, task_2 = sale.tasks_ids
        project = sale.tasks_ids.mapped('project_id')
        timesheet_100_1 = self.env['account.analytic.line'].create({
            'date': '2022-01-01',
            'employee_id': self.employee.id,
            'name': 'Test',
            'unit_amount': 10.0,
            'project_id': project.id,
            'task_id': task_1.id,
        })
        line_1 = sale.order_line.filtered(lambda l: l.qty_delivered == 10.0)
        self.assertTrue(line_1)
        self.assertTrue(line_1.qty_delivered, 10.0)
        line_2 = sale.order_line - line_1
        timesheet_100_2 = self.env['account.analytic.line'].create({
            'date': '2022-01-05',
            'employee_id': self.employee.id,
            'name': 'Test',
            'unit_amount': 90.0,
            'project_id': project.id,
            'task_id': task_1.id,
        })
        self.assertTrue(line_1.qty_delivered, 100.0)
        # create a timesheet for a DIFFERENT employee
        timesheet_100_3 = self.env['account.analytic.line'].create({
            'date': '2022-01-05',
            'employee_id': self.sales_employee.id,
            'name': 'Test',
            'unit_amount': 10.0,
            'project_id': project.id,
            'task_id': task_1.id,
        })
        self.assertTrue(line_1.qty_delivered, 110.0)
        timesheet_150_1 = self.env['account.analytic.line'].create({
            'date': '2022-01-07',
            'employee_id': self.employee.id,
            'name': 'Test',
            'unit_amount': 100.0,
            'project_id': project.id,
            'task_id': task_2.id,
        })
        self.assertTrue(line_2.qty_delivered, 100.0)

        self.assertEqual(sale.invoice_status, 'to invoice', "Should be ready to invoice.")
        wiz = self.env['sale.advance.payment.inv'].with_context(active_ids=sale.ids).create({})
        wiz.create_invoices()
        self.assertTrue(sale.invoice_ids, "Should have an invoice.")
        invoice = sale.invoice_ids
        self.assertEqual(invoice.state, 'draft')
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')
        self.assertTrue(invoice.commission_ids)
        self.assertEqual(len(invoice.commission_ids), 1)

        commission_emp = invoice.commission_ids
        self.assertEqual(commission_emp.amount, 1250.0)
