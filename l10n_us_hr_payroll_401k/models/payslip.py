# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date
from odoo import fields, models


def ee_401k(amount, rate, payslip, categories, worked_days, inputs):
    MAX = payslip.rule_parameter('ee_401k_contribution_limit')
    if payslip.dict.ira_period_age() >= 50:
        MAX += payslip.rule_parameter('ee_401k_catchup')
    wages = categories.BASIC
    year = payslip.date_to.year
    next_year = str(year + 1)
    from_ = str(year) + '-01-01'
    to = next_year + '-01-01'
    ytd = payslip.sum_category('EE_IRA', from_, to)
    ytd += payslip.sum_category('EE_IRA_ROTH', from_, to)
    remaining = MAX + ytd
    if remaining <= 0.0:
        result = 0
    else:
        result = -amount
        result -= (wages * rate) / 100.0
        if remaining + result <= 0.0:
            result = -remaining
    return result


def er_401k_match(wages, payslip, categories, worked_days, inputs):
    MAX = payslip.rule_parameter('er_401k_contribution_limit')
    employee_contrib = -(categories.EE_IRA + categories.EE_IRA_ROTH)

    year = payslip.date_to.year
    next_year = str(year + 1)
    from_ = str(year) + '-01-01'
    to = next_year + '-01-01'
    ytd = payslip.sum_category('ER_IRA', from_, to)

    rate = payslip.contract_id.company_401k_match_percent(payslip)
    wages_match = (wages * rate) / 100.0
    if employee_contrib <= wages_match:
        result = employee_contrib
    else:
        result = wages_match
    remaining = MAX - ytd
    if remaining <= 0.0:
        result = 0
    else:
        if remaining - result < 0.0:
            result = remaining
    return result


class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _age_on_date(self, birthday, cutoff):
        if isinstance(cutoff, str):
            try:
                cutoff = fields.Date.from_string(cutoff)
            except:
                cutoff = None
        if cutoff is None:
            # Dec. 31st in calendar year
            cutoff = date(self.date_to.year, 12, 31)
        if not birthday:
            return -1
        years = cutoff.year - birthday.year
        if birthday.month > cutoff.month or (birthday.month == cutoff.month and birthday.day > cutoff.day):
            years -= 1
        return years

    def ira_period_age(self, cutoff=None):
        birthday = self.employee_id.birthday
        return self._age_on_date(birthday, cutoff)

    def _get_base_local_dict(self):
        res = super()._get_base_local_dict()
        res.update({
            'ee_401k': ee_401k,
            'er_401k_match': er_401k_match,
        })
        return res
