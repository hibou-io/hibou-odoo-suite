# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.
from odoo.exceptions import UserError

# import logging
# _logger = logging.getLogger(__name__)


def _state_applies(payslip, state_code):
    return state_code == payslip.contract_id.us_payroll_config_value('state_code')


def _general_rate(payslip, wage, ytd_wage, wage_base=None, wage_start=None, rate=None):
    """
    Function parameters:
    wage_base, wage_start, rate can either be strings (rule_parameters) or floats
    :return: result, result_rate(wage, percent)
    """

    # Resolve parameters.  On exception, return (probably missing a year, would rather not have exception)
    if wage_base and isinstance(wage_base, str):
        try:
            wage_base = payslip.rule_parameter(wage_base)
        except (KeyError, UserError):
            return 0.0, 0.0

    if wage_start and isinstance(wage_start, str):
        try:
            wage_start = payslip.rule_parameter(wage_start)
        except (KeyError, UserError):
            return 0.0, 0.0

    if rate and isinstance(rate, str):
        try:
            rate = payslip.rule_parameter(rate)
        except (KeyError, UserError):
            return 0.0, 0.0

    if not rate:
        return 0.0, 0.0
    else:
        # Rate assumed positive percentage!
        rate = -rate

    if wage_base:
        remaining = wage_base - ytd_wage
        if remaining < 0.0:
            result = 0.0
        elif remaining < wage:
            result = remaining
        else:
            result = wage

        # _logger.warn('  wage_base method result: ' + str(result) + ' rate: ' + str(rate))
        return result, rate
    if wage_start:
        if ytd_wage >= wage_start:
            # _logger.warn('  wage_start 1 method result: ' + str(wage) + ' rate: ' + str(rate))
            return wage, rate
        if ytd_wage + wage <= wage_start:
            # _logger.warn('  wage_start 2 method result: ' + str(0.0) + ' rate: ' + str(0.0))
            return 0.0, 0.0
        # _logger.warn('  wage_start 3 method result: ' + str((wage - (wage_start - ytd_wage))) + ' rate: ' + str(rate))
        return (wage - (wage_start - ytd_wage)), rate

    # If the wage doesn't have a start or a base
    # _logger.warn('  basic result: ' + str(wage) + ' rate: ' + str(rate))
    return wage, rate


def general_state_unemployment(payslip, categories, worked_days, inputs, wage_base=None, wage_start=None, rate=None, state_code=None):
    """
    Returns SUTA eligible wage and rate.
    WAGE = GROSS - WAGE_US_940_FUTA_EXEMPT

    The contract's `futa_type` determines if SUTA should be collected.

    :return: result, result_rate(wage, percent)
    """

    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    # Determine Eligible.
    if payslip.contract_id.futa_type in (payslip.contract_id.FUTA_TYPE_EXEMPT, payslip.contract_id.FUTA_TYPE_BASIC):
        return 0.0, 0.0

    # Determine Wage
    year = payslip.dict.get_year()
    ytd_wage = payslip.sum_category('GROSS', str(year) + '-01-01', str(year + 1) + '-01-01')
    ytd_wage -= payslip.sum_category('WAGE_US_940_FUTA_EXEMPT', str(year) + '-01-01', str(year + 1) + '-01-01')
    ytd_wage += payslip.contract_id.external_wages

    wage = categories.GROSS - categories.WAGE_US_940_FUTA_EXEMPT
    return _general_rate(payslip, wage, ytd_wage, wage_base=wage_base, wage_start=wage_start, rate=rate)


def general_state_income_withholding(payslip, categories, worked_days, inputs, wage_base=None, wage_start=None, rate=None, state_code=None):
    """
    Returns SUTA eligible wage and rate.
    WAGE = GROSS - WAGE_US_941_FIT_EXEMPT

    The Federal Income Tax Filing status (W4) is used for Exemption.

    :return: result, result_rate (wage, percent)
    """
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    if not payslip.contract_id.us_payroll_config_value('fed_941_fit_w4_filing_status'):
        return 0.0, 0.0

    # Determine Wage
    year = payslip.dict.get_year()
    ytd_wage = payslip.sum_category('GROSS', str(year) + '-01-01', str(year + 1) + '-01-01')
    ytd_wage -= payslip.sum_category('WAGE_US_941_FIT_EXEMPT', str(year) + '-01-01', str(year + 1) + '-01-01')
    ytd_wage += payslip.contract_id.external_wages

    wage = categories.GROSS - categories.WAGE_US_941_FIT_EXEMPT
    return _general_rate(payslip, wage, ytd_wage, wage_base=wage_base, wage_start=wage_start, rate=rate)
