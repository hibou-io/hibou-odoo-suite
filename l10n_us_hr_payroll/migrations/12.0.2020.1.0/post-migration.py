# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo.addons.l10n_us_hr_payroll.migrations.data import FIELDS_CONTRACT_TO_US_PAYROLL_FORMS_2020
from odoo.addons.l10n_us_hr_payroll.migrations.helper import field_exists, \
                                                             temp_field_exists, \
                                                             remove_temp_field, \
                                                             temp_field_values


from odoo import SUPERUSER_ID
from odoo.api import Environment


import logging
_logger = logging.getLogger(__name__)


def migrate(cr, installed_version):
    fields_to_move = [f for f in FIELDS_CONTRACT_TO_US_PAYROLL_FORMS_2020 if temp_field_exists(cr, 'hr_contract', f)]
    if not fields_to_move:
        _logger.warn(' migration aborted because no temporary fields exist...')
        return

    env = Environment(cr, SUPERUSER_ID, {})
    new_structure = env.ref('l10n_us_hr_payroll.structure_type_employee')

    # We will assume all contracts without a struct (because we deleted it), or with one like US_xx_EMP, need config
    contracts = env['hr.contract'].search([
        '|',
        ('struct_id', '=', False),
        ('struct_id.code', '=like', 'US_%'),
    ])
    _logger.warn('Migrating Contracts: ' + str(contracts))
    for contract in contracts:
        _logger.warn('Migrating contract: ' + str(contract) + ' for employee: ' + str(contract.employee_id))
        # Could we somehow detect the state off of the current/orphaned salary structure?
        old_struct_code = contract.struct_id.code
        temp_values = temp_field_values(cr, 'hr_contract', contract.id, fields_to_move)
        # Resolve mapping to the new field names.
        values = {FIELDS_CONTRACT_TO_US_PAYROLL_FORMS_2020[k]: v for k, v in temp_values.items()}
        values.update({
            'name': 'MIG: ' + str(contract.name),
            'employee_id': contract.employee_id.id,
        })
        us_payroll_config = env['hr.contract.us_payroll_config'].create(values)
        contract.write({
            'struct_id': new_structure.id,
            'us_payroll_config_id': us_payroll_config.id,
        })

    for field in fields_to_move:
        remove_temp_field(cr, 'hr_contract', field)
