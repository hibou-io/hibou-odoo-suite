# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

def er_us_940_futa(payslip, categories, worked_days, inputs):
    """
    Returns FUTA eligible wage and rate.
    WAGE = GROSS - WAGE_US_940_FUTA_EXEMPT
    :return: result, result_rate (wage, percent)
    """

    # Determine Rate.
    if payslip.contract_id.futa_type == payslip.contract_id.FUTA_TYPE_EXEMPT:
        # Exit early
        return 0.0, 0.0
    elif payslip.contract_id.futa_type == payslip.contract_id.FUTA_TYPE_BASIC:
        result_rate = -payslip.rule_parameter('fed_940_futa_rate_basic')
    else:
        result_rate = -payslip.rule_parameter('fed_940_futa_rate_normal')

    # Determine Wage
    year = payslip.dict.get_year()
    ytd_wage = payslip.sum_category('GROSS', str(year) + '-01-01', str(year+1) + '-01-01')
    ytd_wage -= payslip.sum_category('WAGE_US_940_FUTA_EXEMPT', str(year) + '-01-01', str(year+1) + '-01-01')
    ytd_wage += payslip.contract_id.external_wages

    wage_base = payslip.rule_parameter('fed_940_futa_wage_base')
    remaining = wage_base - ytd_wage

    wage = categories.GROSS - categories.WAGE_US_940_FUTA_EXEMPT

    if remaining < 0.0:
        result = 0.0
    elif remaining < wage:
        result = remaining
    else:
        result = wage

    return result, result_rate
