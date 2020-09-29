# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import odoo


def migrate(cr, version):
    """
    Post-migration no contracts will have any structure types.
    Unfortunately, we have no way of knowing if they used USA in the past
    so we have to just assume they did (knowing of course that l10n_us_hr_payroll was installed)...
    """
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    structure_type = env.ref('l10n_us_hr_payroll.structure_type_employee')
    cr.execute("UPDATE hr_contract "
               "SET structure_type_id = %s "
               "WHERE structure_type_id is null AND state in ('draft', 'open')", (structure_type.id, ))

    """
    Additionally, it is known that post-migration databases will have bad 
    work entry record states (and you will spend time trying to fix them 
    before you could run a payroll batch).
    """
    default_work_entry_type = env.ref('hr_work_entry.work_entry_type_attendance', raise_if_not_found=False)
    if default_work_entry_type:
        cr.execute("UPDATE hr_work_entry "
                   "SET work_entry_type_id = %s "
                   "WHERE work_entry_type_id is null", (default_work_entry_type.id, ))
    cr.execute("UPDATE hr_work_entry "
               "SET state = 'draft' "
               "WHERE state = 'conflict'")
