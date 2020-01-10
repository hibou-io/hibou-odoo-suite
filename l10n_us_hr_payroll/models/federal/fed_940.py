# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

def er_us_940_futa(payslip, categories, worked_days, inputs):
    """
    Returns FUTA eligible wage and rate.
    WAGE = GROSS + DED_FUTA_EXEMPT
    :return: result, result_rate (wage, percent)
    """

    # Determine Rate.
    if payslip.dict.contract_id.futa_type == payslip.dict.contract_id.FUTA_TYPE_EXEMPT:
        # Exit early
        return 0.0, 0.0
    elif payslip.dict.contract_id.futa_type == payslip.dict.contract_id.FUTA_TYPE_BASIC:
        result_rate = -payslip.dict.rule_parameter('fed_940_futa_rate_basic')
    else:
        result_rate = -payslip.dict.rule_parameter('fed_940_futa_rate_normal')

    # Determine Wage
    year = payslip.dict.get_year()
    ytd_wage = payslip.sum_category('GROSS', str(year) + '-01-01', str(year+1) + '-01-01')
    ytd_wage += payslip.sum_category('DED_FUTA_EXEMPT', str(year) + '-01-01', str(year+1) + '-01-01')
    ytd_wage += payslip.dict.contract_id.external_wages

    wage_base = payslip.dict.rule_parameter('fed_940_futa_wage_base')
    remaining = wage_base - ytd_wage

    wage = categories.GROSS + categories.DED_FUTA_EXEMPT

    if remaining < 0.0:
        result = 0.0
    elif remaining < wage:
        result = remaining
    else:
        result = wage

    return result, result_rate
