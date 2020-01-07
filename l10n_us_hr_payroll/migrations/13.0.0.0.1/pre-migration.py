# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import odoo


def migrate(cr, version):
    """
    Salary Rules can be archived by Odoo S.A. during migration.
    This leaves them archived after the migration, and even un-archiving them
    is not enough because they will then be pointed to a "migrated" structure.
    """
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    xml_refs = env['ir.model.data'].search([
        ('module', '=', 'l10n_us_hr_payroll'),
        ('model', '=', 'hr.salary.rule'),
    ])
    # I don't know why Odoo makes these non-updatable...
    xml_refs.write({'noupdate': False})

    rule_ids = xml_refs.mapped('res_id')
    rules = env['hr.salary.rule'].browse(rule_ids)
    rules.write({'active': True})

    # Cannot add new selection type without fixing missing
    cr.execute('UPDATE hr_payroll_structure SET schedule_pay = \'monthly\' WHERE schedule_pay is null;')
    cr.execute('UPDATE hr_payroll_structure_type SET default_schedule_pay = \'monthly\' WHERE default_schedule_pay is null;')
