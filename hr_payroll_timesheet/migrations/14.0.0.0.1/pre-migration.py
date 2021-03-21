# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import odoo


def migrate(cr, version):
    """
    In 13.0, we had our own work type:
    hr_payroll_timesheet.work_input_timesheet

    This was moved to `hr_timesheet_work_entry`
    We will unlink the XML ref so that the record will be kept.
    """
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    xml_refs = env['ir.model.data'].search([
        ('module', '=', 'hr_payroll_timesheet'),
        ('name', '=', 'work_input_timesheet'),
    ])
    xml_refs.unlink()
