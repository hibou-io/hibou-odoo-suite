# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models

from .federal.ca_fit import ca_fit_federal_income_tax_withholding


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
            'ca_fit_federal_income_tax_withholding': ca_fit_federal_income_tax_withholding,
        })
        return res

    def get_pay_periods_in_year(self):
        return self.PAY_PERIODS_IN_YEAR.get(self.contract_id.schedule_pay, 0)
