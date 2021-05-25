import logging

_logger = logging.getLogger("__name__")

def ca_fit_federal_income_tax_withholding(payslip):
    # annual_taxable_income = _compute_annual_taxable_income(payslip)


    # _logger.warning('payslip.contract_id************************************')
    # _logger.warning(str(payslip.contract_id.read()))
    # _logger.warning('payslip.contract_id.structure_type_id.read()************************************')
    # _logger.warning(str(payslip.contract_id.structure_type_id.read()))
    # _logger.warning('payslip.contract_id.structure_type_id.struct_ids[0].read()************************************')
    # _logger.warning(str(payslip.contract_id.structure_type_id.struct_ids[0].read()))
    # _logger.warning('payslip.contract_id.structure_type_id.struct_ids[0].rule_ids[0].read()************************************')
    # _logger.warning(str(payslip.contract_id.structure_type_id.struct_ids[0].rule_ids[0].read()))
    _logger.warning('payslip.rule_parameter(rule_parameter_ca_fed_tax_rate)************************************')
    _logger.warning(str(payslip.rule_parameter))
    rates = payslip.rule_parameter('ca_fed_tax_rate')['annually'] #this is the hr.rule.parameter code
    # _logger.warning(str(rates))
    wage = payslip.contract_id.wage
    _logger.warning(f'wage = {str(wage)}')
    i = 0
    _logger.warning(f'rates ================================== {str(rates)}')
    for annual_taxable_income, rate, federal_constant in rates:
        if isinstance(annual_taxable_income, str):
            _logger.warning(f'annual_taxable_income is str {annual_taxable_income}')
            _logger.warning(f'wage*rate = {str(wage*rate)}, and rate is {str(rate)}')
            return wage, -rate
        if annual_taxable_income/12 >= wage:
            if i != 0:
                _logger.warning(f'if i != 0')
                rate = rates[i-1][1]*100
                _logger.warning(f'rate = ****************************************  {rate}')
                _logger.warning(f' wage*rate = ***************************************   {wage*rate}')
                return wage, -rate
            else:
                _logger.warning(f'return 0.0, 0.0')
                return 0.0, 0.0
        else:
            _logger.warning(f' annual_taxable_income/12 = {str(annual_taxable_income/12)} which is below wage = {str(str(wage))}*****************************')
            i +=1
            continue






    return 0.0, 0.0