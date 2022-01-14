# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, _general_rate


def _wa_washington_fml(payslip, categories, worked_days, inputs, inner_rate=None):
    if not inner_rate:
        return 0.0, 0.0

    if not _state_applies(payslip, 'WA'):
        return 0.0, 0.0

    wage = categories.GROSS
    year = payslip.dict.get_year()
    ytd_wage = payslip.sum_category('GROSS', str(year) + '-01-01', str(year + 1) + '-01-01')
    ytd_wage += payslip.contract_id.external_wages
    rate = payslip.rule_parameter('us_wa_fml_rate')
    rate *= payslip.rule_parameter(inner_rate) / 100.0
    return _general_rate(payslip, wage, ytd_wage, wage_base='us_wa_fml_wage_base', rate=rate)


def wa_washington_fml_er(payslip, categories, worked_days, inputs):
    return _wa_washington_fml(payslip, categories, worked_days, inputs, inner_rate='us_wa_fml_rate_er')


def wa_washington_fml_ee(payslip, categories, worked_days, inputs):
    return _wa_washington_fml(payslip, categories, worked_days, inputs, inner_rate='us_wa_fml_rate_ee')

def wa_washington_cares_ee(payslip, categories, worked_days, inputs):
    if not _state_applies(payslip, 'WA'):
        return 0.0, 0.0
    wage = categories.GROSS
    rate = payslip.rule_parameter('us_wa_cares_rate_ee')
    # Rate assumed positive percentage!
    return wage, -rate
