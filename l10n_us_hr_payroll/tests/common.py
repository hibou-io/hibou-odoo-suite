# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import timedelta

from odoo.addons.l10n_us_hr_payroll.models.hr_contract import USHRContract

from odoo.addons.hr_payroll_hibou.tests import common


process_payslip = common.process_payslip


class TestUsPayslip(common.TestPayslip):

    def setUp(self):
        super(TestUsPayslip, self).setUp()
        self.structure_type = self.env.ref('l10n_us_hr_payroll.structure_type_employee')
        self.structure = self.env.ref('l10n_us_hr_payroll.hr_payroll_structure')
        # self.structure_type.default_struct_id = self.structure
        self._log('US structue_type  %s and structure  %s' % (self.structure_type, self.structure))

    def _createContract(self, employee, **kwargs):
        # Override
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
                self._logger.warning('cannot locate attribute names "%s" on contract or payroll config' % (key, ))

        # US Payroll Config Defaults Should be set on the Model
        config = config_model.create(config_values)
        contract_values['us_payroll_config_id'] = config.id
        self._get_contract_defaults(contract_values)
        self._log('creating contract with finial values: %s' % (contract_values, ))
        contract = contract_model.create(contract_values)

        # Compatibility with Odoo 13/14
        contract.structure_type_id.default_struct_id.schedule_pay = schedule_pay
        return contract

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
