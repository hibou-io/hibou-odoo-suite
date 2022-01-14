# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage

MAX_ALLOWANCES = 10


def ca_california_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.

    :return: result, result_rate (wage, percent)
    """

    state_code = 'CA'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    filing_status = payslip.contract_id.us_payroll_config_value('ca_de4_sit_filing_status')
    if not filing_status:
        return 0.0, 0.0

    schedule_pay = payslip.contract_id.schedule_pay
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    sit_allowances = payslip.contract_id.us_payroll_config_value('ca_de4_sit_allowances')
    additional_allowances = payslip.contract_id.us_payroll_config_value('ca_de4_sit_additional_allowances')
    low_income_exemption = payslip.rule_parameter('us_ca_sit_income_exemption_rate')[schedule_pay]
    estimated_deduction = payslip.rule_parameter('us_ca_sit_estimated_deduction_rate')[schedule_pay]
    tax_table = payslip.rule_parameter('us_ca_sit_tax_rate')[filing_status].get(schedule_pay)
    standard_deduction = payslip.rule_parameter('us_ca_sit_standard_deduction_rate')[schedule_pay]
    exemption_allowances = payslip.rule_parameter('us_ca_sit_exemption_allowance_rate')[schedule_pay]

    low_income = False
    if filing_status == 'head_household':
        _, _, _, income = low_income_exemption
        if wage <= income:
            low_income = True
    elif filing_status == 'married':
        if sit_allowances >= 2:
            _, _, income, _ = low_income_exemption
            if wage <= income:
                low_income = True
        else:
            _, income, _, _ = low_income_exemption
            if wage <= income:
                low_income = True
    else:
        income, _, _, _ = low_income_exemption
        if wage <= income:
            low_income = True

    withholding = 0.0
    taxable_wage = wage
    if not low_income:
        allowance_index = max(additional_allowances - 1, 0)
        if additional_allowances > MAX_ALLOWANCES:
            deduction = (estimated_deduction[0] * additional_allowances)
            taxable_wage -= deduction
        elif additional_allowances > 0:
            deduction = estimated_deduction[allowance_index]
            taxable_wage -= deduction

        if filing_status == 'head_household':
            _, _, _, deduction = standard_deduction
            taxable_wage -= deduction
        elif filing_status == 'married':
            if sit_allowances >= 2:
                _, _, deduction, _ = standard_deduction
                taxable_wage -= deduction
            else:
                _, deduction, _, _ = standard_deduction
                taxable_wage -= deduction
        else:
            deduction, _, _, _ = standard_deduction
            taxable_wage -= deduction

        over = 0.0
        for row in tax_table:
            if taxable_wage <= row[0]:
                withholding = ((taxable_wage - over) * row[1]) + row[2]
                break
            over = row[0]

        allowance_index = sit_allowances - 1
        if sit_allowances > MAX_ALLOWANCES:
            deduction = exemption_allowances[0] * sit_allowances
            withholding -= deduction
        elif sit_allowances > 0:
            deduction = exemption_allowances[allowance_index]
            withholding -= deduction
    
    if withholding < 0.0:
        withholding = 0.0
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
