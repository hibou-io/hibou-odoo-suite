# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

# import logging
# _logger = logging.getLogger(__name__)


def ee_us_941_fica_ss(payslip, categories, worked_days, inputs):
    """
    Returns FICA Social Security eligible wage and rate.
    WAGE = GROSS - WAGE_US_941_FICA_EXEMPT
    :return: result, result_rate (wage, percent)
    """
    exempt = payslip.contract_id.us_payroll_config_value('fed_941_fica_exempt')
    if exempt:
        return 0.0, 0.0

    # Determine Rate.
    result_rate = -payslip.rule_parameter('fed_941_fica_ss_rate')

    # Determine Wage
    year = payslip.dict.get_year()
    ytd_wage = payslip.sum_category('GROSS', str(year) + '-01-01', str(year+1) + '-01-01')
    ytd_wage -= payslip.sum_category('WAGE_US_941_FICA_EXEMPT', str(year) + '-01-01', str(year+1) + '-01-01')
    ytd_wage += payslip.contract_id.external_wages

    wage_base = payslip.rule_parameter('fed_941_fica_ss_wage_base')
    remaining = wage_base - ytd_wage

    wage = categories.GROSS - categories.WAGE_US_941_FICA_EXEMPT

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
    WAGE = GROSS - WAGE_US_941_FICA_EXEMPT
    :return: result, result_rate (wage, percent)
    """
    exempt = payslip.contract_id.us_payroll_config_value('fed_941_fica_exempt')
    if exempt:
        return 0.0, 0.0

    # Determine Rate.
    result_rate = -payslip.rule_parameter('fed_941_fica_m_rate')

    # Determine Wage
    year = payslip.dict.get_year()
    ytd_wage = payslip.sum_category('GROSS', str(year) + '-01-01', str(year+1) + '-01-01')
    ytd_wage -= payslip.sum_category('WAGE_US_941_FICA_EXEMPT', str(year) + '-01-01', str(year+1) + '-01-01')
    ytd_wage += payslip.contract_id.external_wages

    wage_base = float(payslip.rule_parameter('fed_941_fica_m_wage_base'))  # inf
    remaining = wage_base - ytd_wage

    wage = categories.GROSS - categories.WAGE_US_941_FICA_EXEMPT

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
    Note that this wage is not capped like the above rules.
    WAGE = GROSS - WAGE_FICA_EXEMPT
    :return: result, result_rate (wage, percent)
    """
    exempt = payslip.contract_id.us_payroll_config_value('fed_941_fica_exempt')
    if exempt:
        return 0.0, 0.0

    # Determine Rate.
    result_rate = -payslip.rule_parameter('fed_941_fica_m_add_rate')

    # Determine Wage
    year = payslip.dict.get_year()
    ytd_wage = payslip.sum_category('GROSS', str(year) + '-01-01', str(year+1) + '-01-01')
    ytd_wage -= payslip.sum_category('WAGE_US_941_FICA_EXEMPT', str(year) + '-01-01', str(year+1) + '-01-01')
    ytd_wage += payslip.contract_id.external_wages

    wage_start = payslip.rule_parameter('fed_941_fica_m_add_wage_start')
    existing_wage = ytd_wage - wage_start

    wage = categories.GROSS - categories.WAGE_US_941_FICA_EXEMPT

    if existing_wage >= 0.0:
        result = wage
    elif wage + existing_wage > 0.0:
        result = wage + existing_wage
    else:
        result = 0.0

    return result, result_rate


# Federal Income Tax
def ee_us_941_fit(payslip, categories, worked_days, inputs):
    """
    Returns Wage and rate that is computed given the amount to withhold.
    WAGE = GROSS - WAGE_US_941_FIT_EXEMPT
    :return: result, result_rate (wage, percent)
    """
    filing_status = payslip.contract_id.us_payroll_config_value('fed_941_fit_w4_filing_status')
    if not filing_status:
        return 0.0, 0.0

    schedule_pay = payslip.contract_id.schedule_pay
    wage = categories.GROSS - categories.WAGE_US_941_FIT_EXEMPT
    #_logger.warn('initial gross wage: ' + str(wage))
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
            #_logger.warn('  is_nrm after wage: ' + str(working_wage))

        pay_periods = payslip.dict.get_pay_periods_in_year()
        wage_annual = pay_periods * working_wage
        #_logger.warn('annual wage: ' + str(wage_annual))
        wage_annual += payslip.contract_id.us_payroll_config_value('fed_941_fit_w4_other_income')
        #_logger.warn('  after other income: ' + str(wage_annual))

        deductions = payslip.contract_id.us_payroll_config_value('fed_941_fit_w4_deductions')
        #_logger.warn('deductions from W4: ' + str(deductions))

        higher_rate_type = payslip.contract_id.us_payroll_config_value('fed_941_fit_w4_multiple_jobs_higher')
        if not higher_rate_type:
            deductions += 12900.0 if filing_status == 'married' else 8600.0
            #_logger.warn('  deductions after standard deduction: ' + str(deductions))

        adjusted_wage_annual = wage_annual - deductions
        if adjusted_wage_annual < 0.0:
            adjusted_wage_annual = 0.0
        #_logger.warn('adusted annual wage: ' + str(adjusted_wage_annual))

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
        #_logger.warn('  selected row: ' + str(selected_row))
        working_wage = adjusted_wage_annual - wage_threshold
        tentative_withholding_amount = (working_wage * marginal_rate) + base_withholding_amount
        tentative_withholding_amount = tentative_withholding_amount / pay_periods
        #_logger.warn('tenative withholding amount: ' + str(tentative_withholding_amount))

        # Step 3
        dependent_credit = payslip.contract_id.us_payroll_config_value('fed_941_fit_w4_dependent_credit')
        dependent_credit = dependent_credit / pay_periods
        #_logger.warn('dependent credit (per period): ' + str(dependent_credit))
        tentative_withholding_amount -= dependent_credit
        if tentative_withholding_amount < 0.0:
            tentative_withholding_amount = 0.0

        # Step 4
        withholding_amount = tentative_withholding_amount + payslip.contract_id.us_payroll_config_value('fed_941_fit_w4_additional_withholding')
        #_logger.warn('final withholding amount: ' + str(withholding_amount))
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
