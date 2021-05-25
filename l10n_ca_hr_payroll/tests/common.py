from . import common

import logging
from odoo.addons.hr_payroll_hibou.tests import common

_logger = logging.getLogger("__name__")
#todo need to work in currency


class TestCAPayslip(common.TestPayslip):

    def setUp(self):
        super(TestCAPayslip, self).setUp()
        self.structure_type = self.env.ref('l10n_ca_hr_payroll.ca_structure_type_employee')
        self.structure = self.env.ref('l10n_ca_hr_payroll.hr_ca_payroll_structure')
        self.structure_type.default_struct_id = self.structure
        self._log('US structue_type  %s and structure  %s' % (self.structure_type, self.structure))
        _logger.warning(str(self.structure_type))


    def _createEmployee(self):
        return self.env['hr.employee'].create({
            'birthday': '1985-03-14',
            'country_id': self.ref('base.ca'),
            'department_id': self.ref('hr.dep_rd'),
            'gender': 'male',
            'name': 'Jared'
        })

    def _createCAContract(self, employee, wage=7000, pay_schedule='monthly'):
        country_id = self.env['res.country'].search([('code', '=', 'CA')])
        self.assertEqual(employee.country_id, country_id, 'The employee\'s country_id is not for Canada')

        contract = self._createContract(employee,
                                        wage=wage,
                                        structure_type_id=self.env.ref(
                                            'l10n_ca_hr_payroll.ca_structure_type_employee'),
                                        pay_schedule=pay_schedule)
        self.assertEqual(contract.wage, wage,
                         'The contract salary of "%s" does not equal the test salary of "%s".' % (
                             contract.wage, wage))
        _logger.warning('Created Contract &&&&&&&&&&&&&&&&&&&&&&&')
        return contract

    def get_providence(self):
        pass



    # def get_ca_state(self, code, cache={}):
    #     country_key = 'CA_COUNTRY'
    #     if code in cache:
    #         return cache[code]
    #     if country_key not in cache:
    #         cache[country_key] = self.env.ref('base.ca')
    #     ca_country = cache[country_key]
    #     ca_state = self.env['res.country.state'].search([
    #         ('country_id', '=', ca_country.id),
    #         ('code', '=', code),
    #     ], limit=1)
    #     cache[code] = ca_state
    #     return ca_state






        # _logger.warning(str(payslip.read()))

        # start asserting




    # # to work in shell
    # employee = env['hr.employee'].create({
    #     'birthday': '1985-03-14',
    #     'country_id': env['res.country'].search([('code', '=', 'CA')]).id,
    #     'department_id': env.ref('hr.dep_rd').id,
    #     'gender': 'male',
    #     'name': 'Jared'
    #     })
    # schedule_pay = 'monthly'
    # salary = 80000.0
    # contract_values = {
    #     'wage': salary,
    #     'name': 'Test Contract',
    #     'employee_id': employee.id,
    #     'structure_type_id': env.ref("l10n_ca_hr_payroll.ca_structure_type_employee"),
    #     }
    # contract = env['hr.contract'].create(contract_values)
    # contract.structure_type_id.default_struct_id.schedule_pay = schedule_pay
    # date_from = '2021-01-01'
    # date_to = '2021-01-31'
    # slip = env['hr.payslip'].create({
    #     'name': 'Test %s From: %s To: %s' % (employee.name, date_from, date_to),
    #     'employee_id': employee.id,
    #     'date_from': date_from,
    #     'date_to': date_to
    # })


    # def _createContract(self, employee, **kwargs):
    #     # Override
    #     if not 'schedule_pay' in kwargs:
    #         kwargs['schedule_pay'] = 'monthly'
    #     schedule_pay = kwargs['schedule_pay']
    #     config_model = self.env['hr.contract.us_payroll_config']
    #     contract_model = self.env['hr.contract']
    #     config_values = {
    #         'name': 'Test Config Values',
    #         'employee_id': employee.id,
    #     }
    #     contract_values = {
    #         'name': 'Test Contract',
    #         'employee_id': employee.id,
    #     }
    #
    #     # Backwards compatability with 'futa_type'
    #     if 'futa_type' in kwargs:
    #         kwargs['fed_940_type'] = kwargs['futa_type']
    #
    #     for key, val in kwargs.items():
    #         # Assume any Odoo object is in a Many2one
    #         if hasattr(val, 'id'):
    #             val = val.id
    #         found = False
    #         if hasattr(contract_model, key):
    #             contract_values[key] = val
    #             found = True
    #         if hasattr(config_model, key):
    #             config_values[key] = val
    #             found = True
    #         if not found:
    #             self._logger.warn('cannot locate attribute names "%s" on contract or payroll config' % (key, ))
    #
    #     # US Payroll Config Defaults Should be set on the Model
    #     config = config_model.create(config_values)
    #     contract_values['us_payroll_config_id'] = config.id
    #     self._get_contract_defaults(contract_values)
    #     self._log('creating contract with finial values: %s' % (contract_values, ))
    #     contract = contract_model.create(contract_values)
    #
    #     # Compatibility with Odoo 13/14
    #     contract.structure_type_id.default_struct_id.schedule_pay = schedule_pay
    #     return contract








