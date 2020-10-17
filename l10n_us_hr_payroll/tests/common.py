# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from logging import getLogger
from sys import float_info as sys_float_info
from collections import defaultdict
from datetime import timedelta

from odoo.tests import common
from odoo.tools.float_utils import float_round as odoo_float_round
from odoo.addons.l10n_us_hr_payroll.models.hr_contract import USHRContract


def process_payslip(payslip):
    try:
        payslip.action_payslip_done()
    except AttributeError:
        # v9
        payslip.process_sheet()


class TestUsPayslip(common.TransactionCase):
    debug = False
    _logger = getLogger(__name__)

    def setUp(self):
        super(TestUsPayslip, self).setUp()
        self.env['ir.config_parameter'].set_param('hr_payroll.payslip.sum_behavior', 'date_to')
        self.structure_type_id = self.ref('l10n_us_hr_payroll.structure_type_employee')
        self.resource_calendar_id = self.ref('resource.resource_calendar_std')

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

        # Backwards compatability with 'futa_type'
        if 'futa_type' in kwargs:
            kwargs['fed_940_type'] = kwargs['futa_type']

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
            contract_values['structure_type_id'] = self.structure_type_id
        if not contract_values.get('date_start'):
            contract_values['date_start'] = '2016-01-01'
        if not contract_values.get('date_end'):
            contract_values['date_end'] = '2030-12-31'
        if not contract_values.get('resource_calendar_id'):
            contract_values['resource_calendar_id'] = self.resource_calendar_id

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

    def assertPayrollAlmostEqual(self, first, second):
        self.assertAlmostEqual(first, second, self.payroll_digits-1)

    def get_us_state(self, code, cache={}):
        country_key = 'US_COUNTRY'
        if code in cache:
            return cache[code]
        if country_key not in cache:
            cache[country_key] = self.env.ref('base.us')
        us_country = cache[country_key]
        us_state = self.env['res.country.state'].search([
            ('country_id', '=', us_country.id),
            ('code', '=', code),
        ], limit=1)
        cache[code] = us_state
        return us_state

    def _test_suta(self, category, state_code, rate, date, wage_base=None, relaxed=False, **extra_contract):
        if relaxed:
            _assert = self.assertPayrollAlmostEqual
        else:
            _assert = self.assertPayrollEqual
        if wage_base:
            # Slightly larger than 1/2 the wage_base
            wage = round(wage_base / 2.0) + 100.0
            self.assertTrue((2 * wage) > wage_base, 'Granularity of wage_base too low.')
        else:
            wage = 1000.0

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=wage,
                                        state_id=self.get_us_state(state_code),
                                        **extra_contract)

        rate = -rate / 100.0  # Assumed passed as percent positive

        # Tests
        payslip = self._createPayslip(employee, date, date + timedelta(days=30))

        # Test exemptions
        contract.us_payroll_config_id.fed_940_type = USHRContract.FUTA_TYPE_EXEMPT
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        _assert(cats.get(category, 0.0), 0.0)

        contract.us_payroll_config_id.fed_940_type = USHRContract.FUTA_TYPE_BASIC
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        _assert(cats.get(category, 0.0), 0.0)

        # Test Normal
        contract.us_payroll_config_id.fed_940_type = USHRContract.FUTA_TYPE_NORMAL
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        _assert(cats.get(category, 0.0), wage * rate)
        process_payslip(payslip)

        # Second Payslip
        payslip = self._createPayslip(employee, date + timedelta(days=31), date + timedelta(days=60))
        payslip.compute_sheet()
        cats = self._getCategories(payslip)

        if wage_base:
            remaining_unemp_wages = wage_base - wage
            self.assertTrue((remaining_unemp_wages * rate) <= 0.01)  # less than 0.01 because rate is negative
            _assert(cats.get(category, 0.0), remaining_unemp_wages * rate)

            # As if they were paid once already, so the first "two payslips" would remove all of the tax obligation
            # 1 wage - Payslip (confirmed)
            # 1 wage - external_wages
            # 1 wage - current Payslip
            contract.external_wages = wage
            payslip.compute_sheet()
            cats = self._getCategories(payslip)
            _assert(cats.get(category, 0.0), 0.0)
        else:
            _assert(cats.get(category, 0.0), wage * rate)

    def _test_er_suta(self, state_code, rate, date, wage_base=None, relaxed=False, **extra_contract):
        self._test_suta('ER_US_SUTA', state_code, rate, date, wage_base=wage_base, relaxed=relaxed, **extra_contract)

    def _test_ee_suta(self, state_code, rate, date, wage_base=None, relaxed=False, **extra_contract):
        self._test_suta('EE_US_SUTA', state_code, rate, date, wage_base=wage_base, relaxed=relaxed, **extra_contract)
