# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date
from pprint import pformat

import logging
_logger = logging.getLogger(__name__)


def ir_5ta_cat(payslip, categories, worked_days, inputs):
    if inputs.EE_PE_IR_5TA_CAT:
        # cannot look for amount because it could be forced to zero
        return inputs.EE_PE_IR_5TA_CAT.amount, 100.0
    
    basic_wage = categories.BASIC
    if payslip.dict.contract_id.pe_payroll_config_value('ee_5ta_cat_exempt'):
        return 0.0, 0.0
    
    pay_periods_in_year = payslip.pay_periods_in_year
    uit = payslip.rule_parameter('pe_uit')
    payslip_date_end = payslip.dict.date_to
    
    #    IF this is the last payroll in June or December
    #    THEN we need to 'true up' the last two quarters of withholding (e.g. give a refund)
    last_payslip_june = payslip_date_end.month == 6 and payslip_date_end.day == 30
    # NOTE we do NOT currently support 'catch up' in June.  Our formula genearlly already catches up.
    last_payslip_june = False
    last_payslip_december = payslip_date_end.month == 12 and payslip_date_end.day == 31
    
    wage_period = categories.GROSS
    if not any((basic_wage, wage_period, last_payslip_june, last_payslip_december)):
        return 0.0, 0.0
    
    period_additional_wage = max(wage_period - basic_wage, 0.0)  # 0.0 or positive
    
    year = payslip_date_end.year
    next_year = date(year+1, 1, 1)
    prior_wage_year = payslip.sum_category('GROSS', str(year) + '-01-01', str(year+1) + '-01-01')
    pay_periods_at_current = round(((next_year - payslip_date_end).days / 365) * pay_periods_in_year) + 1.0
    
    wage_year = (basic_wage * pay_periods_at_current) + prior_wage_year
    
    #    IF employee's `first_contract_date` is in current year
    #    THEN we can pro-rate the period (reduce withholding)
    # TODO replace with just date_from on contract or something
    # we are told that every year new contracts will be needed
    date_hired = payslip.dict.contract_id.first_contract_date
    payslip_date_end = payslip.dict.date_to
    hired_in_year = date_hired.year == payslip_date_end.year
    periods_in_year_eligible = pay_periods_in_year
    if hired_in_year:
        periods_in_year_eligible = round(((next_year - date_hired).days / 365) * pay_periods_in_year)
    
    # normalize 1era Gratification
    if hired_in_year and date_hired.month > 6:
        wage_gratif_1 = 0.0
    elif hired_in_year:
        wage_gratif_1 = basic_wage / 6 * (6 - date_hired.month + 1)
    else:
        wage_gratif_1 = basic_wage
    
    # normalize 2da Gratification
    if hired_in_year and date_hired.month > 6:
        wage_gratif_2 = basic_wage / 6 * (12 - date_hired.month + 1)
    else:
        wage_gratif_2 = basic_wage
    
    wage_year += wage_gratif_1 + wage_gratif_2
    cat_ley = (wage_gratif_1 + wage_gratif_2) * (payslip.rule_parameter('ee_ir_5ta_cat_ley_29351') / 100.0)
    wage_year += cat_ley
    wage_year += period_additional_wage
    
    over_7uit = wage_year - (7.0 * uit)
    total_tax = 0.0
    if over_7uit > 0.0:
        total_tax = 0.0
        last_uit = 0.0
        for _uit, rate in payslip.rule_parameter('ee_ir_5ta_cat'):
            # marginal brackets
            _uit = float(_uit)
            if over_7uit > (last_uit * uit):
                eligible_wage = min(over_7uit, _uit * uit) - (last_uit * uit)
                if eligible_wage > 0.0:
                    total_tax += eligible_wage * (rate / 100.0)
                else:
                    break
            else:
                break
            last_uit = _uit

    # if total_tax:
    ytd_tax = -payslip.sum_category('EE_PE_IR_5TA_CAT', str(year) + '-01-01', str(year+1) + '-01-01')
    
    if last_payslip_june or last_payslip_december:
        if last_payslip_june:
            # does not work right because the gratif_2 is already there
            total_tax /= 2
        # remaining_tax may flip signs
        remaining_tax = -(total_tax - ytd_tax)
        if not wage_period:
            # to give refund, cannot normalize to wage
            return remaining_tax, 100.0
        return wage_period,  (remaining_tax / wage_period * 100.0)
    
    tax = -(total_tax - ytd_tax) / pay_periods_at_current
    # uncomment to see a lot of detail
    # _logger.info('ir_5ta_cat locals: ' + str(pformat(locals())))
    return wage_period, (tax / wage_period * 100.0)
