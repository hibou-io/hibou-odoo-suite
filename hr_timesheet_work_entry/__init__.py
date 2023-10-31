from . import models


def ts_work_type_pre_init_hook(cr):
    """
    This module installs a Work Entry Type with code "TS"
    If you have undergone a migration (either for this module
    or even your own Payslip Work Entry lines with code "TS")
    then the uniqueness constraint will prevent this module
    from installing.
    """
    cr.execute("UPDATE hr_work_entry_type "
               "SET code = 'TS-PRE-INSTALL-14' "
               "WHERE code = 'TS';"
               )
