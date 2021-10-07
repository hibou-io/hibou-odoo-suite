# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from logging import getLogger
from sys import float_info as sys_float_info
from collections import defaultdict

from odoo.tests import common
from odoo.tools.float_utils import float_round as odoo_float_round


def process_payslip(payslip):
    try:
        payslip.action_payslip_done()
    except AttributeError:
        # v9
        payslip.process_sheet()


class TestUsPayslip(common.TransactionCase):
    debug = False
    _logger = getLogger(__name__)

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
            self._logger.warn(message)
            
    def _createEmployee(self):
        return self.env['hr.employee'].create({
            'birthday': '1985-03-14',
            'country_id': self.ref('base.us'),
            'department_id': self.ref('hr.dep_rd'),
            'gender': 'male',
            'name': 'Jared'
        })

    def _createContract(self, employee, **kwargs):
        if not 'schedule_pay' in kwargs:
            kwargs['schedule_pay'] = 'monthly'
        schedule_pay = kwargs['schedule_pay']
        config_model = self.env['hr.contract.us_payroll_config']
        contract_model = self.env['hr.contract']
        config_values = {
            'name': 'Test Config Values',
            'employee_id': employee.id,
        }
        contract_values = {
            'name': 'Test Contract',
            'employee_id': employee.id,
        }

        for key, val in kwargs.items():
            # Assume any Odoo object is in a Many2one
            if hasattr(val, 'id'):
                val = val.id
            found = False
            if hasattr(contract_model, key):
                contract_values[key] = val
                found = True
            if hasattr(config_model, key):
                config_values[key] = val
                found = True
            if not found:
                self._logger.warn('cannot locate attribute names "%s" on contract or payroll config' % (key, ))

        # US Payroll Config Defaults Should be set on the Model
        config = config_model.create(config_values)
        contract_values['us_payroll_config_id'] = config.id

        # Some Basic Defaults
        if not contract_values.get('state'):
            contract_values['state'] = 'open'  # Running
        if not contract_values.get('structure_type_id'):
            contract_values['structure_type_id'] = self.ref('l10n_us_hr_payroll.structure_type_employee')
        if not contract_values.get('date_start'):
            contract_values['date_start'] = '2016-01-01'
        if not contract_values.get('date_end'):
            contract_values['date_end'] = '2030-12-31'
        if not contract_values.get('resource_calendar_id'):
            contract_values['resource_calendar_id'] = self.ref('resource.resource_calendar_std')

        # Compatibility with earlier Odoo versions
        if not contract_values.get('journal_id') and hasattr(contract_model, 'journal_id'):
            try:
                contract_values['journal_id'] = self.env['account.journal'].search([('type', '=', 'general')], limit=1).id
            except KeyError:
                # Accounting not installed
                pass

        contract = contract_model.create(contract_values)

        # Compatibility with Odoo 13
        contract.structure_type_id.default_struct_id.schedule_pay = schedule_pay
        return contract

    def _createPayslip(self, employee, date_from, date_to):
        slip = self.env['hr.payslip'].create({
            'name': 'Test %s From: %s To: %s' % (employee.name, date_from, date_to),
            'employee_id': employee.id,
            'date_from': date_from,
            'date_to': date_to
        })
        slip._onchange_employee()
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

    def test_semi_monthly(self):
        salary = 80000.0
        employee = self._createEmployee()
        # so the schedule_pay is now on the Structure...
        contract = self._createContract(employee, wage=salary, schedule_pay='semi-monthly')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-14')

        payslip.compute_sheet()
