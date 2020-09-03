from . import models


def ts_payroll_pre_init_hook(cr):
    """
    This module installs a Work Entry Type with code "TS"
    If you have undergone a migration (either for this module
    or even your own Payslip Work Entry lines with code "TS")
    then the uniqueness constraint will prevent this module
    from installing.
    """
    cr.execute("UPDATE hr_work_entry_type "
               "SET code = 'TS-PRE-INSTALL' "
               "WHERE code = 'TS';"
               )
    cr.execute("UPDATE hr_work_entry_type "
               "SET code = 'TS_OT-PRE-INSTALL' "
               "WHERE code = 'TS_OT';"
               )
