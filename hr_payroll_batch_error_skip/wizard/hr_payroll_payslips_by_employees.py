import logging
from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def _check_undefined_slots(self, work_entries, payslip_run):
        try:
            super()._check_undefined_slots(work_entries, payslip_run)
        except UserError as e:
            _logger.info('Caught user error when checking for undefined slots: ' + str(e))

