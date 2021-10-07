# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models

from .federal.fed_940 import er_us_940_futa
from .federal.fed_941 import ee_us_941_fica_ss, \
                             ee_us_941_fica_m, \
                             ee_us_941_fica_m_add,\
                             er_us_941_fica_ss, \
                             er_us_941_fica_m, \
                             ee_us_941_fit


class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    # From IRS Publication 15-T or logically (annually, bi-monthly)
    PAY_PERIODS_IN_YEAR = {
            'annually':        1,
            'semi-annually':   2,
            'quarterly':       4,
            'bi-monthly':      6,
            'monthly':        12,
            'semi-monthly':   24,
            'bi-weekly':      26,
            'weekly':         52,
            'daily':         260,
        }

    def _get_base_local_dict(self):
        res = super()._get_base_local_dict()
        res.update({
            'er_us_940_futa': er_us_940_futa,
            'ee_us_941_fica_ss': ee_us_941_fica_ss,
            'ee_us_941_fica_m': ee_us_941_fica_m,
            'ee_us_941_fica_m_add': ee_us_941_fica_m_add,
            'er_us_941_fica_ss': er_us_941_fica_ss,
            'er_us_941_fica_m': er_us_941_fica_m,
            'ee_us_941_fit': ee_us_941_fit,
        })
        return res

    def get_year(self):
        # Helper method to get the year (normalized between Odoo Versions)
        return self.date_to.year

    def get_pay_periods_in_year(self):
        return self.PAY_PERIODS_IN_YEAR.get(self.contract_id.schedule_pay, 0)
