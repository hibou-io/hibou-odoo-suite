# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

def ir_5ta_cat(payslip, categories, worked_days, inputs, basic_wage):
    pay_periods_in_year = payslip.pay_periods_in_year
    uit = payslip.rule_parameter('pe_uit')

    # there are two special scenarios
    # 1. IF employee's `date_hired` is in current year
    #    THEN we can pro-rate the period (reduce withholding)
    date_hired = payslip.dict.contract_id.pe_payroll_config_value('date_hired')
    payslip_date_end = payslip.dict.date_to
    hired_in_year = date_hired.year == payslip_date_end.year
    
    # 2. IF this is the last payroll in June or December
    #    THEN we need to 'true up' the last two quarters of withholding (e.g. give a refund)
    last_payslip_june = payslip_date_end.month == 6 and payslip_date_end.day == 30
    last_payslip_december = payslip_date_end.month == 12 and payslip_date_end.day == 31

    # basic_wage = BASIC  # must be paramatarized as we will not have locals
    wage_period = categories.GROSS
    if not all((basic_wage, wage_period)) and not any((last_payslip_june, last_payslip_december)):
        return 0.0, 0.0
    
    period_additional_wage = max(wage_period - basic_wage, 0.0)  # 0.0 or positive
    wage_year = basic_wage * pay_periods_in_year
    # this can be reduced
    remaining_months = 12
    if hired_in_year:
        # e.g. hired in March (3) gives us 12 - 3 + 1 = 10  (Jan, Feb are the 2 missing from 12)
        remaining_months = 12 - date_hired.month + 1
    
    # additional 2 months (July and December) (note 2/12 == 1/6)
    wage_2 = wage_year * (1/6)
    if remaining_months < 6:
        wage_2 = wage_year * (1/12)
    wage_3 = wage_2 * (payslip.rule_parameter('ee_ir_5ta_cat_ley_29351') / 100.0)
    wage_year += wage_2 + wage_3
    # now that we have wage_year, we may need to adjust it by remaining months
    wage_year = wage_year * remaining_months / 12  # could be 12/12
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

    if total_tax:
        if last_payslip_june or last_payslip_december:
            year = payslip_date_end.year
            ytd_tax = -payslip.sum_category('EE_PE_IR_5TA_CAT', str(year) + '-01-01', str(year+1) + '-01-01')
            if last_payslip_june:
                total_tax /= 2
            # remaining_tax may flip signs
            remaining_tax = -(total_tax - ytd_tax)
            return wage_period,  (remaining_tax / wage_period * 100.0)
        tax = -total_tax / remaining_months  # TODO needs to be normalized to periods in year if not monthly...
        return wage_period, (tax / wage_period * 100.0)
    return 0.0, 0.0
