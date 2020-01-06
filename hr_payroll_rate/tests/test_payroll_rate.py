from odoo.tests import common
from odoo import fields


class TestPayrollRate(common.TransactionCase):

    def setUp(self):
        super(TestPayrollRate, self).setUp()
        self.employee = self.env['hr.employee'].create({
            'birthday': '1985-03-14',
            'country_id': self.ref('base.us'),
            'department_id': self.ref('hr.dep_rd'),
            'gender': 'male',
            'name': 'Jared'
        })
        self.contract = self.env['hr.contract'].create({
            'name': 'test',
            'employee_id': self.employee.id,
            'type_id': self.ref('hr_contract.hr_contract_type_emp'),
            'struct_id': self.ref('hr_payroll.structure_base'),
            'resource_calendar_id': self.ref('resource.resource_calendar_std'),
            'wage': 21.50,
            'date_start': '2018-01-01',
            'state': 'open',
            'schedule_pay': 'monthly',
        })
        self.payslip = self.env['hr.payslip'].create({
            'employee_id': self.employee.id,
        })
        self.company_other = self.env['res.company'].create({
            'name': 'Other'
        })

    def test_payroll_rate_basic(self):
        rate = self.payslip.get_rate('TEST')
        self.assertFalse(rate)
        test_rate = self.env['hr.payroll.rate'].create({
            'name': 'Test Rate',
            'code': 'TEST',
            'rate': 1.65,
            'date_from': '2018-01-01',
        })

        rate = self.payslip.get_rate('TEST')
        self.assertEqual(rate, test_rate)

        test_rate.parameter_value = """[
        (1, 2, 3),
        (4, 5, 6),
        ]"""

        value = self.payslip.rule_parameter('TEST')
        self.assertEqual(len(value), 2)
        self.assertEqual(value[0], (1, 2, 3))

    def test_payroll_rate_multicompany(self):
        test_rate_other = self.env['hr.payroll.rate'].create({
            'name': 'Test Rate',
            'code': 'TEST',
            'rate': 1.65,
            'date_from': '2018-01-01',
            'company_id': self.company_other.id,
        })
        rate = self.payslip.get_rate('TEST')
        self.assertFalse(rate)
        test_rate = self.env['hr.payroll.rate'].create({
            'name': 'Test Rate',
            'code': 'TEST',
            'rate': 1.65,
            'date_from': '2018-01-01',
        })

        rate = self.payslip.get_rate('TEST')
        self.assertEqual(rate, test_rate)

        test_rate_more_specific = self.env['hr.payroll.rate'].create({
            'name': 'Test Rate Specific',
            'code': 'TEST',
            'rate': 1.65,
            'date_from': '2018-01-01',
            'company_id': self.payslip.company_id.id,
        })
        rate = self.payslip.get_rate('TEST')
        self.assertEqual(rate, test_rate_more_specific)

    def test_payroll_rate_newer(self):
        test_rate_old = self.env['hr.payroll.rate'].create({
            'name': 'Test Rate',
            'code': 'TEST',
            'rate': 1.65,
            'date_from': '2018-01-01',
        })
        test_rate = self.env['hr.payroll.rate'].create({
            'name': 'Test Rate',
            'code': 'TEST',
            'rate': 2.65,
            'date_from': '2019-01-01',
        })

        rate = self.payslip.get_rate('TEST')
        self.assertEqual(rate, test_rate)

    def test_payroll_rate_precision(self):
        test_rate = self.env['hr.payroll.rate'].create({
            'name': 'Test Rate',
            'code': 'TEST',
            'rate': 2.65001,
            'date_from': '2019-01-01',
        })
        self.assertEqual(round(test_rate.rate * 100000), 265001.0)
