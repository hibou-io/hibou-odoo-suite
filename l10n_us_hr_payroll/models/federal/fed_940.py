# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.


def futa_wage(payslip, categories):
    """
    Returns FUTA eligible wage for current Payslip (no wage_base, just by categories)
    WAGE = GROSS - ALW_FUTA_EXEMPT + DED_FUTA_EXEMPT
    :return: wage
    """
    wage = categories.GROSS

    wage -= categories.ALW_FUTA_EXEMPT + \
            categories.ALW_FIT_FUTA_EXEMPT + \
            categories.ALW_FIT_FICA_FUTA_EXEMPT + \
            categories.ALW_FICA_FUTA_EXEMPT

    wage += categories.DED_FUTA_EXEMPT + \
            categories.DED_FIT_FUTA_EXEMPT + \
            categories.DED_FIT_FICA_FUTA_EXEMPT + \
            categories.DED_FICA_FUTA_EXEMPT

    return wage


def futa_wage_ytd(payslip, categories):
    """
    Returns Year to Date FUTA eligible wages
    WAGE = GROSS - ALW_FUTA_EXEMPT + DED_FUTA_EXEMPT
    :return: wage
    """
    year = payslip.dict.get_year()
    ytd_wage = payslip.sum_category('GROSS',                     str(year) + '-01-01', str(year+1) + '-01-01')

    ytd_wage -= payslip.sum_category('ALW_FUTA_EXEMPT',          str(year) + '-01-01', str(year+1) + '-01-01') + \
                payslip.sum_category('ALW_FIT_FUTA_EXEMPT',      str(year) + '-01-01', str(year+1) + '-01-01') + \
                payslip.sum_category('ALW_FIT_FICA_FUTA_EXEMPT', str(year) + '-01-01', str(year+1) + '-01-01') + \
                payslip.sum_category('ALW_FICA_FUTA_EXEMPT',     str(year) + '-01-01', str(year+1) + '-01-01')

    ytd_wage += payslip.sum_category('DED_FUTA_EXEMPT',          str(year) + '-01-01', str(year+1) + '-01-01') + \
                payslip.sum_category('DED_FIT_FUTA_EXEMPT',      str(year) + '-01-01', str(year+1) + '-01-01') + \
                payslip.sum_category('DED_FIT_FICA_FUTA_EXEMPT', str(year) + '-01-01', str(year+1) + '-01-01') + \
                payslip.sum_category('DED_FICA_FUTA_EXEMPT',     str(year) + '-01-01', str(year+1) + '-01-01')

    ytd_wage += payslip.contract_id.external_wages
    return ytd_wage


def er_us_940_futa(payslip, categories, worked_days, inputs):
    """
    Returns FUTA eligible wage and rate.
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
    wage = futa_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    ytd_wage = futa_wage_ytd(payslip, categories)
    wage_base = payslip.rule_parameter('fed_940_futa_wage_base')
    remaining = wage_base - ytd_wage

    if remaining < 0.0:
        result = 0.0
    elif remaining < wage:
        result = remaining
    else:
        result = wage

    return result, result_rate
