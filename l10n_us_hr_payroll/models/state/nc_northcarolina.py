# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def nc_northcarolina_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.
    WAGE = GROSS + DED_FIT_EXEMPT

    :return: result, result_rate (wage, percent)
    """
    state_code = 'NC'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    filing_status = payslip.contract_id.us_payroll_config_value('nc_nc4_sit_filing_status')
    if not filing_status:
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    schedule_pay = payslip.contract_id.schedule_pay
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    allowances = payslip.contract_id.us_payroll_config_value('nc_nc4_sit_allowances')
    allowances_rate = payslip.rule_parameter('us_nc_sit_allowance_rate').get(schedule_pay)['allowance']
    deduction = payslip.rule_parameter('us_nc_sit_allowance_rate').get(schedule_pay)['standard_deduction'] if filing_status != 'head_household' else payslip.rule_parameter('us_nc_sit_allowance_rate').get(schedule_pay)['standard_deduction_hh']

    taxable_wage = round((wage - (deduction + (allowances * allowances_rate))) * 0.0535)
    withholding = 0.0
    if taxable_wage < 0.0:
        withholding -= taxable_wage
    withholding = taxable_wage
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
