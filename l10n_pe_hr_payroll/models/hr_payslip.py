# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models
from .rules.general import _general_rate
from .rules.ir_4ta_cat import ir_4ta_cat
from .rules.ir_5ta_cat import ir_5ta_cat


class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _get_base_local_dict(self):
        res = super()._get_base_local_dict()
        res.update({
            'general_rate': _general_rate,
            'ir_4ta_cat': ir_4ta_cat,
            'ir_5ta_cat': ir_5ta_cat,
        })
        return res
