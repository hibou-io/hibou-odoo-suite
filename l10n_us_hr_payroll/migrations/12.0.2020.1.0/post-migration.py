# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo.addons.l10n_us_hr_payroll.migrations.data import FIELDS_CONTRACT_TO_US_PAYROLL_FORMS_2020, \
                                                           XMLIDS_COPY_ACCOUNTING_2020
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

    def get_state(code, cache={}):
        country_key = 'US_COUNTRY'
        if code in cache:
            return cache[code]
        if country_key not in cache:
            cache[country_key] = env.ref('base.us')
        us_country = cache[country_key]
        us_state = env['res.country.state'].search([
            ('country_id', '=', us_country.id),
            ('code', '=', code),
        ], limit=1)
        cache[code] = us_state
        return us_state

    # We will assume all contracts without a struct (because we deleted it), or with one like US_xx_EMP, need config
    contracts = env['hr.contract'].search([
        ('employee_id', '!=', False),
        '|',
        ('struct_id', '=', False),
        ('struct_id.code', '=like', 'US_%'),
    ])
    _logger.warn('Migrating Contracts: ' + str(contracts))
    for contract in contracts:
        _logger.warn('Migrating contract: ' + str(contract) + ' for employee: ' + str(contract.employee_id))
        if not contract.employee_id.id:
            _logger.warn('  unable to migrate for missing employee id')
            continue
        # Could we somehow detect the state off of the current/orphaned salary structure?
        state_code = False
        old_struct_code = contract.struct_id.code
        if old_struct_code:
            state_code = old_struct_code.split('_')[1]
        temp_values = temp_field_values(cr, 'hr_contract', contract.id, fields_to_move)
        # Resolve mapping to the new field names.
        values = {FIELDS_CONTRACT_TO_US_PAYROLL_FORMS_2020[k]: v for k, v in temp_values.items()}

        # Edge cases
        if 'ca_de4_sit_filing_status' in values and values['ca_de4_sit_filing_status'] == 'exempt':
            values['ca_de4_sit_filing_status'] = ''

        values.update({
            'name': 'MIG: ' + str(contract.name),
            'employee_id': contract.employee_id.id,
            'state_id': get_state(state_code).id,
        })
        us_payroll_config = env['hr.contract.us_payroll_config'].create(values)
        contract.write({
            'struct_id': new_structure.id,
            'us_payroll_config_id': us_payroll_config.id,
        })

    for field in fields_to_move:
        remove_temp_field(cr, 'hr_contract', field)

    # Some added rules should have the same accounting side effects of other migrated rules
    # To ease the transition, we will copy the accounting fields from one to the other.
    rule_model = env['hr.salary.rule']
    if hasattr(rule_model, 'account_debit'):
        for source, destinations in XMLIDS_COPY_ACCOUNTING_2020.items():
            source_rule = env.ref(source, raise_if_not_found=False)
            if source_rule:
                for destination in destinations:
                    destination_rule = env.ref(destination, raise_if_not_found=False)
                    if destination_rule:
                        _logger.warn('Mirgrating accounting from rule: ' + source + ' to rule: ' + destination)
                        destination_rule.write({
                            'account_debit': source_rule.account_debit.id,
                            'account_credit': source_rule.account_credit.id,
                            'account_tax_id': source_rule.account_tax_id.id,
                            'analytic_account_id': source_rule.analytic_account_id.id,
                        })