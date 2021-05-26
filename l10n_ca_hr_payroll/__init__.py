# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from . import models

def _post_install_hook(cr, registry):
    """
        This method will set the default for the Payslip Sum Behavior
    """
    cr.execute("SELECT id FROM ir_config_parameter WHERE key = 'hr_payroll.payslip.sum_behavior';")
    existing = cr.fetchall()
    if not existing:
        cr.execute("INSERT INTO ir_config_parameter (key, value) VALUES ('hr_payroll.payslip.sum_behavior', 'date');")
