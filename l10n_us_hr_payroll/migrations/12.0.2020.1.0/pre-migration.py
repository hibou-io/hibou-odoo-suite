# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo.addons.l10n_us_hr_payroll.migrations.data import FIELDS_CONTRACT_TO_US_PAYROLL_FORMS_2020, \
                                                           XMLIDS_TO_REMOVE_2020, \
                                                           XMLIDS_TO_RENAME_2020
from odoo.addons.l10n_us_hr_payroll.migrations.helper import field_exists, \
                                                             temp_field_exists, \
                                                             make_temp_field, \
                                                             remove_xmlid, \
                                                             rename_xmlid


def migrate(cr, installed_version):
    # Add temporary columns for all hr_contract fields that move to hr_contract_us_payroll_config
    fields_to_move = [f for f in FIELDS_CONTRACT_TO_US_PAYROLL_FORMS_2020 if field_exists(cr, 'hr_contract', f)]
    # Prevent error if repeatedly running and already copied.
    fields_to_move = [f for f in fields_to_move if not temp_field_exists(cr, 'hr_contract', f)]
    for field in fields_to_move:
        make_temp_field(cr, 'hr_contract', field)

    # Need to migrate XMLIDs..
    for xmlid in XMLIDS_TO_REMOVE_2020:
        remove_xmlid(cr, xmlid)

    for from_xmlid, to_xmlid in XMLIDS_TO_RENAME_2020.items():
        rename_xmlid(cr, from_xmlid, to_xmlid)

    # Need to remove views as they don't work anymore.
    cr.execute("DELETE FROM ir_ui_view as v WHERE v.id in (SELECT t.res_id FROM ir_model_data as t WHERE t.model = 'ir.ui.view' and (t.module = 'l10n_us_hr_payroll' or t.module like 'l10n_us_%_hr_payroll'))")
