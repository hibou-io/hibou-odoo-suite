def _state_applies(payslip, state_code):
    return state_code == payslip.contract_id.ca_payroll_config_value('state_code')


# Export for eval context
is_ca_state = _state_applies
