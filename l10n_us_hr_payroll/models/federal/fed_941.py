# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

# import logging
# _logger = logging.getLogger(__name__)


def fica_wage(payslip, categories):
    """
    Returns FICA eligible wage for current Payslip (no wage_base, just by categories)
    WAGE = GROSS - ALW_FICA_EXEMPT + DED_FICA_EXEMPT
    :return: wage
    """
    wage = categories.GROSS

    less_exempt = categories.ALW_FICA_EXEMPT + \
                  categories.ALW_FIT_FICA_EXEMPT + \
                  categories.ALW_FIT_FICA_FUTA_EXEMPT + \
                  categories.ALW_FICA_FUTA_EXEMPT

    plus_exempt = categories.DED_FICA_EXEMPT + \
                  categories.DED_FIT_FICA_EXEMPT + \
                  categories.DED_FIT_FICA_FUTA_EXEMPT + \
                  categories.DED_FICA_FUTA_EXEMPT
    # _logger.info('fica wage GROSS: %0.2f less exempt ALW: %0.2f plus exempt DED: %0.2f' % (wage, less_exempt, plus_exempt))
    return wage - less_exempt + plus_exempt


def fica_wage_ytd(payslip, categories):
    """
    Returns Year to Date FICA eligible wages
    WAGE = GROSS - ALW_FICA_EXEMPT + DED_FICA_EXEMPT
    :return: wage
    """
    year = payslip.dict.get_year()
    ytd_wage = payslip.sum_category('GROSS',                     str(year) + '-01-01', str(year+1) + '-01-01')

    less_exempt = payslip.sum_category('ALW_FICA_EXEMPT',          str(year) + '-01-01', str(year+1) + '-01-01') + \
                  payslip.sum_category('ALW_FIT_FICA_EXEMPT',      str(year) + '-01-01', str(year+1) + '-01-01') + \
                  payslip.sum_category('ALW_FIT_FICA_FUTA_EXEMPT', str(year) + '-01-01', str(year+1) + '-01-01') + \
                  payslip.sum_category('ALW_FICA_FUTA_EXEMPT',     str(year) + '-01-01', str(year+1) + '-01-01')

    plus_exempt = payslip.sum_category('DED_FICA_EXEMPT',          str(year) + '-01-01', str(year+1) + '-01-01') + \
                  payslip.sum_category('DED_FIT_FICA_EXEMPT',      str(year) + '-01-01', str(year+1) + '-01-01') + \
                  payslip.sum_category('DED_FIT_FICA_FUTA_EXEMPT', str(year) + '-01-01', str(year+1) + '-01-01') + \
                  payslip.sum_category('DED_FICA_FUTA_EXEMPT',     str(year) + '-01-01', str(year+1) + '-01-01')

    external_wages = payslip.dict.contract_id.external_wages
    # _logger.info('fica ytd wage GROSS: %0.2f less exempt ALW: %0.2f plus exempt DED: %0.2f plus external: %0.2f' % (ytd_wage, less_exempt, plus_exempt, external_wages))
    return ytd_wage - less_exempt + plus_exempt + external_wages


def ee_us_941_fica_ss(payslip, categories, worked_days, inputs):
    """
    Returns FICA Social Security eligible wage and rate.
    :return: result, result_rate (wage, percent)
    """
    exempt = payslip.contract_id.us_payroll_config_value('fed_941_fica_exempt')
    if exempt:
        return 0.0, 0.0

    # Determine Rate.
    result_rate = -payslip.rule_parameter('fed_941_fica_ss_rate')

    # Determine Wage
    wage = fica_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    ytd_wage = fica_wage_ytd(payslip, categories)
    wage_base = payslip.rule_parameter('fed_941_fica_ss_wage_base')
    remaining = wage_base - ytd_wage

    if remaining < 0.0:
        result = 0.0
    elif remaining < wage:
        result = remaining
    else:
        result = wage

    return result, result_rate


er_us_941_fica_ss = ee_us_941_fica_ss


def ee_us_941_fica_m(payslip, categories, worked_days, inputs):
    """
    Returns FICA Medicare eligible wage and rate.
    :return: result, result_rate (wage, percent)
    """
    exempt = payslip.contract_id.us_payroll_config_value('fed_941_fica_exempt')
    if exempt:
        return 0.0, 0.0

    # Determine Rate.
    result_rate = -payslip.rule_parameter('fed_941_fica_m_rate')

    # Determine Wage
    wage = fica_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    ytd_wage = fica_wage_ytd(payslip, categories)
    wage_base = float(payslip.rule_parameter('fed_941_fica_m_wage_base'))  # inf
    remaining = wage_base - ytd_wage

    if remaining < 0.0:
        result = 0.0
    elif remaining < wage:
        result = remaining
    else:
        result = wage

    return result, result_rate


er_us_941_fica_m = ee_us_941_fica_m


def ee_us_941_fica_m_add(payslip, categories, worked_days, inputs):
    """
    Returns FICA Medicare Additional eligible wage and rate.
    :return: result, result_rate (wage, percent)
    """
    exempt = payslip.contract_id.us_payroll_config_value('fed_941_fica_exempt')
    if exempt:
        return 0.0, 0.0

    # Determine Rate.
    result_rate = -payslip.rule_parameter('fed_941_fica_m_add_rate')

    # Determine Wage
    wage = fica_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    ytd_wage = fica_wage_ytd(payslip, categories)
    wage_start = payslip.rule_parameter('fed_941_fica_m_add_wage_start')
    existing_wage = ytd_wage - wage_start

    if existing_wage >= 0.0:
        result = wage
    elif wage + existing_wage > 0.0:
        result = wage + existing_wage
    else:
        result = 0.0

    return result, result_rate


def fit_wage(payslip, categories):
    """
    Returns FIT eligible wage for current Payslip (no wage_base, just by categories)
    WAGE = GROSS - ALW_FIT_EXEMPT + DED_FIT_EXEMPT
    :return: wage
    """
    wage = categories.GROSS

    wage -= categories.ALW_FIT_EXEMPT + \
            categories.ALW_FIT_FICA_EXEMPT + \
            categories.ALW_FIT_FICA_FUTA_EXEMPT + \
            categories.ALW_FIT_FUTA_EXEMPT

    wage += categories.DED_FIT_EXEMPT + \
            categories.DED_FIT_FICA_EXEMPT + \
            categories.DED_FIT_FICA_FUTA_EXEMPT + \
            categories.DED_FIT_FUTA_EXEMPT

    return wage


def fit_wage_ytd(payslip, categories):
    """
    Returns Year to Date FIT eligible wages
    WAGE = GROSS - ALW_FIT_EXEMPT + DED_FIT_EXEMPT
    :return: wage
    """
    year = payslip.dict.get_year()
    ytd_wage = payslip.sum_category('GROSS',                     str(year) + '-01-01', str(year+1) + '-01-01')

    ytd_wage -= payslip.sum_category('ALW_FIT_EXEMPT',           str(year) + '-01-01', str(year+1) + '-01-01') + \
                payslip.sum_category('ALW_FIT_FICA_EXEMPT',      str(year) + '-01-01', str(year+1) + '-01-01') + \
                payslip.sum_category('ALW_FIT_FICA_FUTA_EXEMPT', str(year) + '-01-01', str(year+1) + '-01-01') + \
                payslip.sum_category('ALW_FIT_FUTA_EXEMPT',      str(year) + '-01-01', str(year+1) + '-01-01')

    ytd_wage += payslip.sum_category('DED_FIT_EXEMPT',           str(year) + '-01-01', str(year+1) + '-01-01') + \
                payslip.sum_category('DED_FIT_FICA_EXEMPT',      str(year) + '-01-01', str(year+1) + '-01-01') + \
                payslip.sum_category('DED_FIT_FICA_FUTA_EXEMPT', str(year) + '-01-01', str(year+1) + '-01-01') + \
                payslip.sum_category('DED_FIT_FUTA_EXEMPT',      str(year) + '-01-01', str(year+1) + '-01-01')

    ytd_wage += payslip.contract_id.external_wages
    return ytd_wage


# Federal Income Tax
def ee_us_941_fit(payslip, categories, worked_days, inputs):
    """
    Returns Wage and rate that is computed given the amount to withhold.
    :return: result, result_rate (wage, percent)
    """
    filing_status = payslip.contract_id.us_payroll_config_value('fed_941_fit_w4_filing_status')
    if not filing_status:
        return 0.0, 0.0

    schedule_pay = payslip.contract_id.schedule_pay
    wage = fit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    #_logger.warning('initial gross wage: ' + str(wage))
    year = payslip.dict.get_year()
    if year >= 2020:
        # Large changes in Federal Income Tax in 2020 and the W4
        # We will assume that your W4 is the 2020 version
        # Steps are from IRS Publication 15-T
        #
        # Step 1
        working_wage = wage
        is_nra = payslip.contract_id.us_payroll_config_value('fed_941_fit_w4_is_nonresident_alien')
        if is_nra:
            nra_table = payslip.rule_parameter('fed_941_fit_nra_additional')
            working_wage += nra_table.get(schedule_pay, 0.0)
            #_logger.warning('  is_nrm after wage: ' + str(working_wage))

        pay_periods = payslip.dict.get_pay_periods_in_year()
        wage_annual = pay_periods * working_wage
        #_logger.warning('annual wage: ' + str(wage_annual))
        wage_annual += payslip.contract_id.us_payroll_config_value('fed_941_fit_w4_other_income')
        #_logger.warning('  after other income: ' + str(wage_annual))

        deductions = payslip.contract_id.us_payroll_config_value('fed_941_fit_w4_deductions')
        #_logger.warning('deductions from W4: ' + str(deductions))

        higher_rate_type = payslip.contract_id.us_payroll_config_value('fed_941_fit_w4_multiple_jobs_higher')
        if not higher_rate_type:
            deductions += 12900.0 if filing_status == 'married' else 8600.0
            #_logger.warning('  deductions after standard deduction: ' + str(deductions))

        adjusted_wage_annual = wage_annual - deductions
        if adjusted_wage_annual < 0.0:
            adjusted_wage_annual = 0.0
        #_logger.warning('adusted annual wage: ' + str(adjusted_wage_annual))

        # Step 2
        if filing_status == 'single':
            tax_tables = payslip.rule_parameter('fed_941_fit_table_single')
        elif filing_status == 'married':
            tax_tables = payslip.rule_parameter('fed_941_fit_table_married')
        else:
            # married_as_single for historic reasons
            tax_tables = payslip.rule_parameter('fed_941_fit_table_hh')

        if higher_rate_type:
            tax_table = tax_tables['higher']
        else:
            tax_table = tax_tables['standard']

        selected_row = None
        for row in tax_table:
            if row[0] <= adjusted_wage_annual:
                selected_row = row
            else:
                # First row where wage is higher than adjusted_wage_annual
                break

        wage_threshold, base_withholding_amount, marginal_rate = selected_row
        #_logger.warning('  selected row: ' + str(selected_row))
        working_wage = adjusted_wage_annual - wage_threshold
        tentative_withholding_amount = (working_wage * marginal_rate) + base_withholding_amount
        tentative_withholding_amount = tentative_withholding_amount / pay_periods
        #_logger.warning('tenative withholding amount: ' + str(tentative_withholding_amount))

        # Step 3
        dependent_credit = payslip.contract_id.us_payroll_config_value('fed_941_fit_w4_dependent_credit')
        dependent_credit = dependent_credit / pay_periods
        #_logger.warning('dependent credit (per period): ' + str(dependent_credit))
        tentative_withholding_amount -= dependent_credit
        if tentative_withholding_amount < 0.0:
            tentative_withholding_amount = 0.0

        # Step 4
        withholding_amount = tentative_withholding_amount + payslip.contract_id.us_payroll_config_value('fed_941_fit_w4_additional_withholding')
        #_logger.warning('final withholding amount: ' + str(withholding_amount))
        # Ideally we would set the 'taxable wage' as the result and compute the percentage tax.
        # This is off by 1 penny across our tests, but I feel like it is worth it for the added reporting.
        # - Jared Kipe 2019 during Odoo 13.0 rewrite.
        #
        # return -withholding_amount, 100.0
        return wage, -(withholding_amount / wage * 100.0)
    else:
        working_wage = wage
        is_nra = payslip.contract_id.us_payroll_config_value('fed_941_fit_w4_is_nonresident_alien')
        if is_nra:
            nra_table = payslip.rule_parameter('fed_941_fit_nra_additional')
            working_wage += nra_table[schedule_pay]

        allowance_table = payslip.rule_parameter('fed_941_fit_allowance')
        allowances = payslip.contract_id.us_payroll_config_value('fed_941_fit_w4_allowances')
        working_wage -= allowance_table[schedule_pay] * allowances
        tax = 0.0
        last_limit = 0.0
        if filing_status == 'married':
            tax_table = payslip.rule_parameter('fed_941_fit_table_married')
        else:
            tax_table = payslip.rule_parameter('fed_941_fit_table_single')
        for row in tax_table[schedule_pay]:
            limit, base, percent = row
            limit = float(limit)  # 'inf'
            if working_wage <= limit:
                tax = base + ((working_wage - last_limit) * (percent / 100.0))
                break
            last_limit = limit

        tax += payslip.contract_id.us_payroll_config_value('fed_941_fit_w4_additional_withholding')
        # Ideally we would set the 'taxable wage' as the result and compute the percentage tax.
        # This is off by 1 penny across our tests, but I feel like it is worth it for the added reporting.
        # - Jared Kipe 2019 during Odoo 13.0 rewrite.
        #
        # return -tax, 100.0
        return wage, -(tax / wage * 100.0)
