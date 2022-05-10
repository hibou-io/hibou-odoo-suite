# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo.addons.hr_payroll_hibou.tests import common


process_payslip = common.process_payslip


class TestPePayslip(common.TestPayslip):

    def setUp(self):
        super().setUp()
        self.structure_type = self.env.ref('l10n_pe_hr_payroll.structure_type_employee')
        self.structure = self.env.ref('l10n_pe_hr_payroll.hr_payroll_structure')
        self.structure_type.default_struct_id = self.structure
        # self.debug = True
        self._log('PE structue_type  %s %s and structure  %s %s' % (self.structure_type, self.structure_type.name, self.structure, self.structure.name))
        self.country_pe = self.env.ref('base.pe')
        
    def _createEmployee(self):
        employee = super()._createEmployee()
        employee.country_id = self.country_pe
        return employee

    def _createContract(self, employee, **kwargs):
        if not 'schedule_pay' in kwargs:
            kwargs['schedule_pay'] = 'monthly'
        
        config_model = self.env['hr.contract.pe_payroll_config']
        schedule_pay = kwargs['schedule_pay']
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
            if hasattr(config_model, key):
                config_values[key] = val
                found = True
            if hasattr(self.contract_model, key):
                contract_values[key] = val
                found = True
            if not found:
                self._logger.warning('cannot locate attribute names "%s" on hr.contract().' % (key, ))

        # PE Payroll Config Defaults Should be set on the Model
        if 'date_hired' not in config_values:
            config_values['date_hired'] = '2016-01-01'
        config = config_model.create(config_values)
        contract_values['pe_payroll_config_id'] = config.id

        self._get_contract_defaults(contract_values)
        contract = self.contract_model.create(contract_values)

        # Compatibility with Odoo 14
        contract.structure_type_id.default_struct_id.schedule_pay = schedule_pay
        return contract
