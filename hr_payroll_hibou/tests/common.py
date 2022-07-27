# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from logging import getLogger
from sys import float_info as sys_float_info
from collections import defaultdict

from odoo.tests import common
from odoo.tools.float_utils import float_round as odoo_float_round


def process_payslip(payslip):
    try:
        return payslip.action_payslip_done()
    except AttributeError:
        # v9
        return payslip.process_sheet()


class TestPayslip(common.TransactionCase):
    debug = False
    _logger = getLogger(__name__)

    def process_payslip(self, payslip=None):
        if not payslip:
            return process_payslip(self.payslip)
        return process_payslip(payslip)

    def setUp(self):
        super(TestPayslip, self).setUp()
        self.contract_model = self.env['hr.contract']
        self.env.user.tz = 'PST8PDT'
        self.env.ref('resource.resource_calendar_std').tz = 'PST8PDT'
        self.env['ir.config_parameter'].set_param('hr_payroll.payslip.sum_behavior', 'date_to')
        self.structure_type = self.env['hr.payroll.structure.type'].create({
            'name': 'Test Structure Type',
        })
        self.structure = self.env['hr.payroll.structure'].create({
            'name': 'Test Structure',
            'type_id': self.structure_type.id,
        })
        self._log('structue_type  %s and structure  %s' % (self.structure_type, self.structure))
        self.structure_type.default_struct_id = self.structure
        self.resource_calendar = self.ref('resource.resource_calendar_std')

    float_info = sys_float_info

    def float_round(self, value, digits):
        return odoo_float_round(value, digits)

    _payroll_digits = -1

    @property
    def payroll_digits(self):
        if self._payroll_digits == -1:
            self._payroll_digits = self.env['decimal.precision'].precision_get('Payroll')
        return self._payroll_digits

    def _log(self, message):
        if self.debug:
            self._logger.warning(message)
            
    def _createEmployee(self):
        employee = self.env['hr.employee'].create({
            'birthday': '1985-03-14',
            'country_id': self.ref('base.us'),
            'department_id': self.ref('hr.dep_rd'),
            'gender': 'male',
            'name': 'Jared'
        })
        employee.address_home_id = self.env['res.partner'].create({
            'name': 'Jared (private)',
        })
        return employee

    def _get_contract_defaults(self, contract_values):
        if not contract_values.get('state'):
            contract_values['state'] = 'open'  # Running
        if not contract_values.get('structure_type_id'):
            contract_values['structure_type_id'] = self.structure_type.id
        if not contract_values.get('date_start'):
            contract_values['date_start'] = '2016-01-01'
        if not contract_values.get('date_end'):
            contract_values['date_end'] = '2030-12-31'
        if not contract_values.get('resource_calendar_id'):
            contract_values['resource_calendar_id'] = self.resource_calendar

        # Compatibility with earlier Odoo versions
        if not contract_values.get('journal_id') and hasattr(self.contract_model, 'journal_id'):
            try:
                contract_values['journal_id'] = self.env['account.journal'].search([('type', '=', 'general')], limit=1).id
            except KeyError:
                # Accounting not installed
                pass

    def _createContract(self, employee, **kwargs):
        if not 'schedule_pay' in kwargs:
            kwargs['schedule_pay'] = 'monthly'
        schedule_pay = kwargs['schedule_pay']
        contract_values = {
            'name': 'Test Contract',
            'employee_id': employee.id,
        }

        for key, val in kwargs.items():
            # Assume any Odoo object is in a Many2one
            if hasattr(val, 'id'):
                val = val.id
            found = False
            if hasattr(self.contract_model, key):
                contract_values[key] = val
                found = True
            if not found:
                self._logger.warning('cannot locate attribute names "%s" on hr.contract().' % (key, ))

        self._get_contract_defaults(contract_values)
        contract = self.contract_model.create(contract_values)

        # Compatibility with Odoo 14
        contract.structure_type_id.default_struct_id.schedule_pay = schedule_pay
        return contract

    def _createPayslip(self, employee, date_from, date_to, skip_compute=False, other_values=False):
        if not other_values:
            other_values = {}
        create_values = {
            'name': 'Test %s From: %s To: %s' % (employee.name, date_from, date_to),
            'employee_id': employee.id,
            'date_from': date_from,
            'date_to': date_to
        }
        create_values.update(other_values)
        slip = self.env['hr.payslip'].create(create_values)
        # Included in hr.payslip.action_refresh_from_work_entries() as ov 14.0 EE
        # slip._onchange_employee()
        # as is the 'compute' that is almost always called immediaately after
        if not skip_compute:
            slip.action_refresh_from_work_entries()
        return slip

    def _getCategories(self, payslip):
        categories = defaultdict(float)
        for line in payslip.line_ids:
            self._log(' line code: ' + str(line.code) +
                      ' category code: ' + line.category_id.code +
                      ' total: ' + str(line.total) +
                      ' rate: ' + str(line.rate) +
                      ' amount: ' + str(line.amount))
            category_id = line.category_id
            category_code = line.category_id.code
            while category_code:
                categories[category_code] += line.total
                category_id = category_id.parent_id
                category_code = category_id.code
        return categories

    def _getRules(self, payslip):
        rules = defaultdict(float)
        for line in payslip.line_ids:
            rules[line.code] += line.total
        return rules

    def assertPayrollEqual(self, first, second):
        self.assertAlmostEqual(first, second, self.payroll_digits)

    def assertPayrollAlmostEqual(self, first, second):
        self.assertAlmostEqual(first, second, self.payroll_digits-1)
