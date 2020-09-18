from . import models


def attn_payroll_pre_init_hook(cr):
    """
    This module installs a Work Entry Type with code "ATTN"
    If you have undergone a migration (either for this module
    or even your own Payslip Work Entry lines with code "ATTN")
    then the uniqueness constraint will prevent this module
    from installing.
    """
    cr.execute("UPDATE hr_work_entry_type "
               "SET code = 'ATTN-PRE-INSTALL' "
               "WHERE code = 'ATTN';"
               )
