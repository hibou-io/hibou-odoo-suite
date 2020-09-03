
def migrate(cr, version):
    # pre_init_hook script only runs on install,
    # if you're coming from 12.0 we need the same change
    from odoo.addons.hr_payroll_timesheet import attn_payroll_pre_init_hook
    attn_payroll_pre_init_hook(cr)
