# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

FIELDS_CONTRACT_TO_US_PAYROLL_FORMS_2020 = {
    # Federal
    'w4_allowances': 'fed_941_fit_w4_allowances',
    'w4_filing_status': 'fed_941_fit_w4_filing_status',
    'w4_is_nonresident_alien': 'fed_941_fit_w4_is_nonresident_alien',
    'w4_additional_withholding': 'fed_941_fit_w4_additional_withholding',
    'fica_exempt': 'fed_941_fica_exempt',
    'futa_type': 'fed_940_type',
    # State
    'al_a4_filing_status': 'al_a4_sit_exemptions',
    'al_a4_dependents': 'al_a4_sit_dependents',
    'al_a4_personal_exemption': 'state_income_tax_exempt',
    'al_a4_additional_wh': 'state_income_tax_additional_withholding',
    
    'ar_w4_allowances': 'ar_ar4ec_sit_allowances',
    'ar_w4_tax_exempt': 'state_income_tax_exempt',
    'ar_w4_additional_wh': 'state_income_tax_additional_withholding',

    'az_a4_withholding_percentage': 'az_a4_sit_withholding_percentage',
    'az_a4_additional_withholding': 'state_income_tax_additional_withholding',

    'ca_de4_allowances': 'ca_de4_sit_allowances',
    'ca_additional_allowances': 'ca_de4_sit_additional_allowances',
    'ca_de4_filing_status': 'ca_de4_sit_filing_status',

    'ct_w4na_code': 'ct_w4na_sit_code',
    'ct_w4na_wh_amount': 'state_income_tax_additional_withholding',

    'ga_g4_filing_status': 'ga_g4_sit_filing_status',
    'ga_g4_dependent_allowances': 'ga_g4_sit_dependent_allowances',
    'ga_g4_additional_allowances': 'ga_g4_sit_additional_allowances',
    'ga_g4_additional_wh': 'state_income_tax_additional_withholding',

    'ia_w4_allowances': 'ia_w4_sit_allowances',
    'ia_w4_additional_wh': 'state_income_tax_additional_withholding',
    'ia_w4_tax_exempt': 'state_income_tax_exempt',

    'id_w4_filing_status': 'id_w4_sit_filing_status',
    'id_w4_allowances': 'id_w4_sit_allowances',

    'il_w4_basic_allowances': 'il_w4_sit_basic_allowances',
    'il_w4_additional_allowances': 'il_w4_sit_additional_allowances',
    'il_w4_additional_wh': 'state_income_tax_additional_withholding',

    'mi_w4_exemptions': 'mi_w4_sit_exemptions',
    'mi_w4_tax_exempt': 'state_income_tax_exempt',
    'mi_w4_additional_wh': 'state_income_tax_additional_withholding',

    'mn_w4mn_filing_status': 'mn_w4mn_sit_filing_status',
    'mn_w4mn_allowances': 'mn_w4mn_sit_allowances',
    'mn_w4mn_additional_wh': 'state_income_tax_additional_withholding',

    'mo_mow4_filing_status': 'mo_mow4_sit_filing_status',
    'mo_mow4_additional_withholding': 'state_income_tax_additional_withholding',

    'ms_89_350_filing_status': 'ms_89_350_sit_filing_status',
    'ms_89_350_exemption': 'ms_89_350_sit_exemption_value',
    'ms_89_350_additional_withholding': 'state_income_tax_additional_withholding',

    'mt_mw4_additional_withholding': 'state_income_tax_additional_withholding',
    'mt_mw4_exemptions': 'mt_mw4_sit_exemptions',
    'mt_mw4_exempt': 'mt_mw4_sit_exempt',

    'nc_nc4_filing_status': 'nc_nc4_sit_filing_status',
    'nc_nc4_allowances': 'nc_nc4_sit_allowances',
    'nc_nc4_additional_wh': 'state_income_tax_additional_withholding',

    'nj_njw4_filing_status': 'nj_njw4_sit_filing_status',
    'nj_njw4_allowances': 'nj_njw4_sit_allowances',
    'nj_njw4_rate_table': 'nj_njw4_sit_rate_table',
    'nj_additional_withholding': 'state_income_tax_additional_withholding',

    'oh_additional_withholding': 'state_income_tax_additional_withholding',
    'oh_income_allowances': 'oh_it4_sit_exemptions',

    'pa_additional_withholding': 'state_income_tax_additional_withholding',

    'va_va4_exemptions': 'va_va4_sit_exemptions',

}

XMLIDS_TO_REMOVE_2020 = [
    # Federal
    # Categories -- These are now all up in the EE FICA or ER FICA
    'l10n_us_hr_payroll.hr_payroll_fica_emp_m',
    'l10n_us_hr_payroll.hr_payroll_fica_emp_m_add',
    'l10n_us_hr_payroll.hr_payroll_fica_emp_m_add_wages',
    'l10n_us_hr_payroll.hr_payroll_fica_comp_m',
    'l10n_us_hr_payroll.hr_payroll_futa_wages',
    'l10n_us_hr_payroll.hr_payroll_fica_emp_m_wages',
    'l10n_us_hr_payroll.hr_payroll_fica_emp_ss_wages',
    # Rules -- These are mainly Wage rules or were simplified to a single rule
    'l10n_us_hr_payroll.hr_payroll_rules_fica_emp_ss_wages_2018',
    'l10n_us_hr_payroll.hr_payroll_rules_fica_emp_m_wages_2018',
    'l10n_us_hr_payroll.hr_payroll_rules_fica_emp_m_add_wages_2018',
    'l10n_us_hr_payroll.hr_payroll_rules_futa_wages_2018',
    'l10n_us_hr_payroll.hr_payroll_rules_fed_inc_withhold_2018_married',
    # State
    'l10n_us_ak_hr_payroll.hr_payroll_ak_unemp_wages',
    'l10n_us_ak_hr_payroll.hr_payroll_ak_unemp',
    'l10n_us_ak_hr_payroll.hr_payroll_ak_unemp_ee',
    'l10n_us_ak_hr_payroll.hr_payroll_rules_ak_unemp_wages',

    'l10n_us_al_hr_payroll.hr_payroll_al_unemp_wages',
    'l10n_us_al_hr_payroll.hr_payroll_al_unemp',
    'l10n_us_al_hr_payroll.hr_payroll_al_income_withhold',
    'l10n_us_al_hr_payroll.hr_payroll_rules_al_unemp_wages',

    'l10n_us_ar_hr_payroll.hr_payroll_ar_unemp_wages',
    'l10n_us_ar_hr_payroll.hr_payroll_ar_unemp',
    'l10n_us_ar_hr_payroll.hr_payroll_ar_income_withhold',
    'l10n_us_ar_hr_payroll.hr_payroll_rules_ar_unemp_wages',

    'l10n_us_az_hr_payroll.hr_payroll_az_unemp_wages',
    'l10n_us_az_hr_payroll.hr_payroll_az_unemp',
    'l10n_us_az_hr_payroll.hr_payroll_az_income_withhold',
    'l10n_us_az_hr_payroll.hr_payroll_rules_az_unemp_wages',

    'l10n_us_ca_hr_payroll.res_partner_cador_ett',
    'l10n_us_ca_hr_payroll.res_partner_cador_sdi',
    'l10n_us_ca_hr_payroll.hr_payroll_ca_uit_wages',
    'l10n_us_ca_hr_payroll.hr_payroll_ca_uit',
    'l10n_us_ca_hr_payroll.hr_payroll_ca_ett_wages',
    'l10n_us_ca_hr_payroll.hr_payroll_ca_ett',
    'l10n_us_ca_hr_payroll.hr_payroll_ca_sdi_wages',
    'l10n_us_ca_hr_payroll.hr_payroll_ca_sdi',
    'l10n_us_ca_hr_payroll.hr_payroll_ca_income_withhold',
    'l10n_us_ca_hr_payroll.hr_payroll_rules_ca_uit_wages_2018',
    'l10n_us_ca_hr_payroll.hr_payroll_rules_ca_ett_wages_2018',
    'l10n_us_ca_hr_payroll.hr_payroll_rules_ca_sdi_wages_2018',

    'l10n_us_ct_hr_payroll.hr_payroll_ct_unemp_wages',
    'l10n_us_ct_hr_payroll.hr_payroll_ct_unemp',
    'l10n_us_ct_hr_payroll.hr_payroll_ct_income_withhold',
    'l10n_us_ct_hr_payroll.hr_payroll_rules_ct_unemp_wages',

    'l10n_us_fl_hr_payroll.hr_payroll_fl_unemp_wages',
    'l10n_us_fl_hr_payroll.hr_payroll_fl_unemp',
    'l10n_us_fl_hr_payroll.hr_payroll_rules_fl_unemp_wages_2018',

    'l10n_us_ga_hr_payroll.hr_payroll_ga_unemp_wages',
    'l10n_us_ga_hr_payroll.hr_payroll_ga_unemp',
    'l10n_us_ga_hr_payroll.hr_payroll_ga_income_withhold',
    'l10n_us_ga_hr_payroll.hr_payroll_rules_ga_unemp_wages',

    'l10n_us_ia_hr_payroll.hr_payroll_ia_unemp_wages',
    'l10n_us_ia_hr_payroll.hr_payroll_ia_unemp',
    'l10n_us_ia_hr_payroll.hr_payroll_ia_income_withhold',
    'l10n_us_ia_hr_payroll.hr_payroll_rules_ia_unemp_wages',

    'l10n_us_id_hr_payroll.hr_payroll_id_unemp_wages',
    'l10n_us_id_hr_payroll.hr_payroll_id_unemp',
    'l10n_us_id_hr_payroll.hr_payroll_id_income_withhold',
    'l10n_us_id_hr_payroll.hr_payroll_rules_id_unemp_wages',

    'l10n_us_il_hr_payroll.hr_payroll_il_unemp_wages',
    'l10n_us_il_hr_payroll.hr_payroll_il_unemp',
    'l10n_us_il_hr_payroll.hr_payroll_il_income_withhold',
    'l10n_us_il_hr_payroll.hr_payroll_rules_il_unemp_wages',

    'l10n_us_mi_hr_payroll.hr_payroll_mi_unemp_wages',
    'l10n_us_mi_hr_payroll.hr_payroll_mi_unemp',
    'l10n_us_mi_hr_payroll.hr_payroll_mi_income_withhold',
    'l10n_us_mi_hr_payroll.hr_payroll_rules_mi_unemp_wages',

    'l10n_us_mn_hr_payroll.hr_payroll_mn_unemp_wages',
    'l10n_us_mn_hr_payroll.hr_payroll_mn_unemp',
    'l10n_us_mn_hr_payroll.hr_payroll_mn_income_withhold',
    'l10n_us_mn_hr_payroll.hr_payroll_rules_mn_unemp_wages',

    'l10n_us_mo_hr_payroll.hr_payroll_mo_unemp_wages',
    'l10n_us_mo_hr_payroll.hr_payroll_mo_unemp',
    'l10n_us_mo_hr_payroll.hr_payroll_mo_income_withhold',
    'l10n_us_mo_hr_payroll.hr_payroll_rules_mo_unemp_wages_2018',

    'l10n_us_ms_hr_payroll.hr_payroll_ms_unemp_wages',
    'l10n_us_ms_hr_payroll.hr_payroll_ms_unemp',
    'l10n_us_ms_hr_payroll.hr_payroll_ms_income_withhold',
    'l10n_us_ms_hr_payroll.hr_payroll_rules_ms_unemp_wages',

    'l10n_us_mt_hr_payroll.hr_payroll_mt_unemp_wages',
    'l10n_us_mt_hr_payroll.hr_payroll_mt_unemp',
    'l10n_us_mt_hr_payroll.hr_payroll_mt_income_withhold',
    'l10n_us_mt_hr_payroll.hr_payroll_rules_mt_unemp_wages',

    'l10n_us_nc_hr_payroll.hr_payroll_nc_unemp_wages',
    'l10n_us_nc_hr_payroll.hr_payroll_nc_unemp',
    'l10n_us_nc_hr_payroll.hr_payroll_nc_income_withhold',
    'l10n_us_nc_hr_payroll.hr_payroll_rules_nc_unemp_wages_2018',

    'l10n_us_nj_hr_payroll.res_partner_njdor_unemp_company',
    'l10n_us_nj_hr_payroll.res_partner_njdor_sdi_employee',
    'l10n_us_nj_hr_payroll.res_partner_njdor_sdi_company',
    'l10n_us_nj_hr_payroll.res_partner_njdor_fli',
    'l10n_us_nj_hr_payroll.res_partner_njdor_wf',
    'l10n_us_nj_hr_payroll.contrib_register_njdor_unemp_company',
    'l10n_us_nj_hr_payroll.contrib_register_njdor_sdi_employee',
    'l10n_us_nj_hr_payroll.contrib_register_njdor_sdi_company',
    'l10n_us_nj_hr_payroll.contrib_register_njdor_fli',
    'l10n_us_nj_hr_payroll.contrib_register_njdor_wf',
    'l10n_us_nj_hr_payroll.hr_payroll_nj_unemp_wages',
    'l10n_us_nj_hr_payroll.hr_payroll_nj_sdi_wages',
    'l10n_us_nj_hr_payroll.hr_payroll_nj_fli_wages',
    'l10n_us_nj_hr_payroll.hr_payroll_nj_wf_wages',
    'l10n_us_nj_hr_payroll.hr_payroll_nj_unemp_employee',
    'l10n_us_nj_hr_payroll.hr_payroll_nj_unemp_company',
    'l10n_us_nj_hr_payroll.hr_payroll_nj_sdi_company',
    'l10n_us_nj_hr_payroll.hr_payroll_nj_sdi_employee',
    'l10n_us_nj_hr_payroll.hr_payroll_nj_fli',
    'l10n_us_nj_hr_payroll.hr_payroll_nj_wf',
    'l10n_us_nj_hr_payroll.hr_payroll_nj_wf_company',
    'l10n_us_nj_hr_payroll.hr_payroll_nj_income_withhold',
    'l10n_us_nj_hr_payroll.hr_payroll_rules_nj_unemp_wages_2018',
    'l10n_us_nj_hr_payroll.hr_payroll_rules_nj_sdi_wages_2018',
    'l10n_us_nj_hr_payroll.hr_payroll_rules_nj_fli_wages_2018',
    'l10n_us_nj_hr_payroll.hr_payroll_rules_nj_wf_wages_2018',

    'l10n_us_oh_hr_payroll.hr_payroll_oh_unemp_wages',
    'l10n_us_oh_hr_payroll.hr_payroll_oh_unemp',
    'l10n_us_oh_hr_payroll.hr_payroll_oh_income_withhold',
    'l10n_us_oh_hr_payroll.hr_payroll_rules_oh_unemp_wages_2018',

    'l10n_us_pa_hr_payroll.res_partner_pador_unemp_employee',
    'l10n_us_pa_hr_payroll.contrib_register_pador_unemp_employee',
    'l10n_us_pa_hr_payroll.hr_payroll_pa_unemp_wages',
    'l10n_us_pa_hr_payroll.hr_payroll_pa_unemp_employee',
    'l10n_us_pa_hr_payroll.hr_payroll_pa_unemp_company',
    'l10n_us_pa_hr_payroll.hr_payroll_pa_withhold',
    'l10n_us_pa_hr_payroll.hr_payroll_rules_pa_unemp_wages_2018',
    'l10n_us_pa_hr_payroll.hr_payroll_rules_pa_inc_withhold_add',

    'l10n_us_sc_hr_payroll.hr_payroll_sc_unemp_wages',
    'l10n_us_sc_hr_payroll.hr_payroll_sc_unemp',
    'l10n_us_sc_hr_payroll.hr_payroll_sc_income_withhold',
    'l10n_us_sc_hr_payroll.hr_payroll_rules_sc_unemp_wages',

    'l10n_us_tx_hr_payroll.contrib_register_txdor',
    'l10n_us_tx_hr_payroll.hr_payroll_tx_unemp_wages',
    'l10n_us_tx_hr_payroll.hr_payroll_tx_unemp',
    'l10n_us_tx_hr_payroll.hr_payroll_tx_oa',
    'l10n_us_tx_hr_payroll.hr_payroll_tx_etia',
    'l10n_us_tx_hr_payroll.hr_payroll_rules_tx_unemp_wages_2018',

    'l10n_us_va_hr_payroll.hr_payroll_va_unemp_wages',
    'l10n_us_va_hr_payroll.hr_payroll_va_unemp',
    'l10n_us_va_hr_payroll.hr_payroll_va_income_withhold',
    'l10n_us_va_hr_payroll.hr_payroll_rules_va_unemp_wages_2018',

    'l10n_us_wa_hr_payroll.hr_payroll_wa_unemp_wages',
    'l10n_us_wa_hr_payroll.hr_payroll_wa_unemp',
    'l10n_us_wa_hr_payroll.hr_payroll_wa_lni',
    'l10n_us_wa_hr_payroll.hr_payroll_wa_lni_withhold',
    'l10n_us_wa_hr_payroll.hr_payroll_rules_wa_unemp_wages_2018',

    'l10n_us_wy_hr_payroll.hr_payroll_wy_unemp_wages',
    'l10n_us_wy_hr_payroll.hr_payroll_wy_unemp',
    'l10n_us_wy_hr_payroll.hr_payroll_rules_wy_unemp_wages'

]

XMLIDS_TO_RENAME_2020 = {
    # Federal
    'l10n_us_hr_payroll.hr_payroll_futa': 'l10n_us_hr_payroll.hr_payroll_category_er_fed_940',
    'l10n_us_hr_payroll.hr_payroll_fica_emp_ss': 'l10n_us_hr_payroll.hr_payroll_category_ee_fed_941',
    'l10n_us_hr_payroll.hr_payroll_fed_income_withhold': 'l10n_us_hr_payroll.hr_payroll_category_ee_fed_941_fit',
    'l10n_us_hr_payroll.hr_payroll_fica_comp_ss': 'l10n_us_hr_payroll.hr_payroll_category_er_fed_941',
    'l10n_us_hr_payroll.hr_payroll_rules_fica_emp_ss_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_fed_941_ss',
    'l10n_us_hr_payroll.hr_payroll_rules_fica_emp_m_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_fed_941_m',
    'l10n_us_hr_payroll.hr_payroll_rules_fica_emp_m_add_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_fed_941_m_add',
    'l10n_us_hr_payroll.hr_payroll_rules_futa_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_fed_940',
    'l10n_us_hr_payroll.hr_payroll_rules_fica_comp_ss': 'l10n_us_hr_payroll.hr_payroll_rule_er_fed_941_ss',
    'l10n_us_hr_payroll.hr_payroll_rules_fica_comp_m': 'l10n_us_hr_payroll.hr_payroll_rule_er_fed_941_m',
    'l10n_us_hr_payroll.hr_payroll_rules_fed_inc_withhold_2018_single': 'l10n_us_hr_payroll.hr_payroll_rule_ee_fed_941_fit',
    # State
    'l10n_us_ak_hr_payroll.res_partner_ak_dlwd_unemp': 'l10n_us_hr_payroll.res_partner_us_ak_dor',
    'l10n_us_ak_hr_payroll.contrib_register_ak_dlwd_unemp': 'l10n_us_hr_payroll.contrib_register_us_ak_dor',
    'l10n_us_ak_hr_payroll.hr_payroll_rules_ak_unemp': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_ak_suta',
    'l10n_us_ak_hr_payroll.hr_payroll_rules_ak_unemp_ee': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_ak_sit',

    'l10n_us_al_hr_payroll.res_partner_al_dol_unemp': 'l10n_us_hr_payroll.res_partner_us_al_dor',
    'l10n_us_al_hr_payroll.res_partner_al_dor_withhold': 'l10n_us_hr_payroll.res_partner_us_al_dor_sit',
    'l10n_us_al_hr_payroll.contrib_register_al_dol_unemp': 'l10n_us_hr_payroll.contrib_register_us_al_dor',
    'l10n_us_al_hr_payroll.contrib_register_al_dor_withhold': 'l10n_us_hr_payroll.contrib_register_us_al_dor_sit',
    'l10n_us_al_hr_payroll.hr_payroll_rules_al_unemp': 'l10n_us_hr_payroll.hr_payroll_rules_az_unemp',
    'l10n_us_al_hr_payroll.hr_payroll_rules_al_inc_withhold': 'l10n_us_hr_payroll.hr_payroll_rules_az_inc_withhold',

    'l10n_us_ar_hr_payroll.res_partner_ar_dws_unemp': 'l10n_us_hr_payroll.res_partner_us_ar_dor',
    'l10n_us_ar_hr_payroll.res_partner_ar_dfa_withhold': 'l10n_us_hr_payroll.res_partner_us_ar_dor_sit',
    'l10n_us_ar_hr_payroll.contrib_register_ar_dws_unemp': 'l10n_us_hr_payroll.contrib_register_us_ar_dor',
    'l10n_us_ar_hr_payroll.contrib_register_ar_dfa_withhold': 'l10n_us_hr_payroll.contrib_register_us_ar_dor_sit',
    'l10n_us_ar_hr_payroll.hr_payroll_rules_ar_unemp': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_ar_suta',
    'l10n_us_ar_hr_payroll.hr_payroll_rules_ar_inc_withhold': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_ar_sit',

    'l10n_us_az_hr_payroll.res_partner_az_des_unemp': 'l10n_us_hr_payroll.res_partner_us_az_dor',
    'l10n_us_az_hr_payroll.res_partner_az_dor_withhold': 'l10n_us_hr_payroll.res_partner_us_az_dor_sit',
    'l10n_us_az_hr_payroll.contrib_register_az_des_unemp': 'l10n_us_hr_payroll.contrib_register_us_az_dor',
    'l10n_us_az_hr_payroll.contrib_register_az_dor_withhold': 'l10n_us_hr_payroll.contrib_register_us_az_dor_sit',
    'l10n_us_az_hr_payroll.hr_payroll_az_unemp': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_az_suta',
    'l10n_us_az_hr_payroll.hr_payroll_az_income_withhold': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_az_sit',

    'l10n_us_ca_hr_payroll.res_partner_cador_uit': 'l10n_us_hr_payroll.res_partner_us_ca_dor',
    'l10n_us_ca_hr_payroll.res_partner_cador_withhold': 'l10n_us_hr_payroll.res_partner_us_ca_dor_sit',
    'l10n_us_ca_hr_payroll.contrib_register_cador_uit': 'l10n_us_hr_payroll.contrib_register_us_ca_dor',
    'l10n_us_ca_hr_payroll.contrib_register_cador_withhold': 'l10n_us_hr_payroll.contrib_register_us_ca_dor_sit',
    'l10n_us_ca_hr_payroll.hr_payroll_rules_ca_uit_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_ca_suta',
    'l10n_us_ca_hr_payroll.hr_payroll_rules_ca_ett_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_ca_ett_suta',
    'l10n_us_ca_hr_payroll.hr_payroll_rules_ca_sdi_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_ca_sdi_sit',
    'l10n_us_ca_hr_payroll.hr_payroll_rules_ca_inc_withhold_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_ca_sit',

    'l10n_us_ct_hr_payroll.res_partner_ct_dol_unemp': 'l10n_us_hr_payroll.res_partner_us_ct_dor',
    'l10n_us_ct_hr_payroll.res_partner_ct_drs_withhold': 'l10n_us_hr_payroll.res_partner_us_ct_dor_sit',
    'l10n_us_ct_hr_payroll.contrib_register_ct_dol_unemp': 'l10n_us_hr_payroll.contrib_register_us_ct_dor',
    'l10n_us_ct_hr_payroll.contrib_register_ct_drs_withhold': 'l10n_us_hr_payroll.contrib_register_us_ct_dor_sit',
    'l10n_us_ct_hr_payroll.hr_payroll_rules_ct_unemp': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_ct_suta',
    'l10n_us_ct_hr_payroll.hr_payroll_rules_ct_inc_withhold': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_ct_sit',

    'l10n_us_fl_hr_payroll.hr_payroll_rules_fl_unemp_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_fl_suta',
    'l10n_us_fl_hr_payroll.res_partner_fldor': 'l10n_us_hr_payroll.res_partner_us_fl_dor',
    'l10n_us_fl_hr_payroll.contrib_register_fldor': 'l10n_us_hr_payroll.contrib_register_us_fl_dor',

    'l10n_us_ga_hr_payroll.res_partner_ga_dol_unemp': 'l10n_us_hr_payroll.res_partner_us_ga_dor',
    'l10n_us_ga_hr_payroll.res_partner_ga_dor_withhold': 'l10n_us_hr_payroll.res_partner_us_ga_dor_sit',
    'l10n_us_ga_hr_payroll.contrib_register_ga_dol_unemp': 'l10n_us_hr_payroll.contrib_register_us_ga_dor',
    'l10n_us_ga_hr_payroll.contrib_register_ga_dor_withhold': 'l10n_us_hr_payroll.contrib_register_us_ga_dor_sit',
    'l10n_us_ga_hr_payroll.hr_payroll_rules_ga_unemp': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_ga_suta',
    'l10n_us_ga_hr_payroll.hr_payroll_rules_ga_inc_withhold': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_ga_sit',

    'l10n_us_ia_hr_payroll.res_partner_ia_wd_unemp': 'l10n_us_hr_payroll.res_partner_us_ia_dor',
    'l10n_us_ia_hr_payroll.res_partner_ia_dor_withhold': 'l10n_us_hr_payroll.res_partner_us_ia_dor_sit',
    'l10n_us_ia_hr_payroll.contrib_register_ia_wd_unemp': 'l10n_us_hr_payroll.contrib_register_us_ia_dor',
    'l10n_us_ia_hr_payroll.contrib_register_ia_dor_withhold': 'l10n_us_hr_payroll.contrib_register_us_ia_dor_sit',
    'l10n_us_ia_hr_payroll.hr_payroll_rules_ia_unemp': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_ia_suta',
    'l10n_us_ia_hr_payroll.hr_payroll_rules_ia_inc_withhold': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_ia_sit',

    'l10n_us_id_hr_payroll.res_partner_id_dol_unemp':'l10n_us_hr_payroll.res_partner_us_id_dor',
    'l10n_us_id_hr_payroll.res_partner_id_stc_withhold': 'l10n_us_hr_payroll.res_partner_us_id_dor_sit',
    'l10n_us_id_hr_payroll.contrib_register_id_dol_unemp': 'l10n_us_hr_payroll.contrib_register_us_id_dor',
    'l10n_us_id_hr_payroll.contrib_register_id_stc_withhold': 'l10n_us_hr_payroll.contrib_register_us_id_dor_sit',
    'l10n_us_id_hr_payroll.hr_payroll_rules_id_unemp': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_id_suta',
    'l10n_us_id_hr_payroll.hr_payroll_rules_id_inc_withhold': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_id_sit',

    'l10n_us_il_hr_payroll.res_partner_il_des_unemp': 'l10n_us_hr_payroll.res_partner_us_il_dor',
    'l10n_us_il_hr_payroll.res_partner_il_dor_withhold': 'l10n_us_hr_payroll.res_partner_us_il_dor_sit',
    'l10n_us_il_hr_payroll.contrib_register_il_des_unemp': 'l10n_us_hr_payroll.contrib_register_us_il_dor',
    'l10n_us_il_hr_payroll.contrib_register_il_dor_withhold': 'l10n_us_hr_payroll.contrib_register_us_il_dor_sit',
    'l10n_us_il_hr_payroll.hr_payroll_rules_il_unemp': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_il_suta',
    'l10n_us_il_hr_payroll.hr_payroll_rules_il_inc_withhold': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_il_sit',

    'l10n_us_mi_hr_payroll.res_partner_mi_uia_unemp': 'l10n_us_hr_payroll.res_partner_us_mi_dor',
    'l10n_us_mi_hr_payroll.res_partner_mi_dot_withhold': 'l10n_us_hr_payroll.res_partner_us_mi_dor_sit',
    'l10n_us_mi_hr_payroll.contrib_register_mi_uia_unemp': 'l10n_us_hr_payroll.contrib_register_us_mi_dor',
    'l10n_us_mi_hr_payroll.contrib_register_mi_dot_withhold': 'l10n_us_hr_payroll.contrib_register_us_mi_dor_sit',
    'l10n_us_mi_hr_payroll.hr_payroll_rules_mi_unemp': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_mi_suta',
    'l10n_us_mi_hr_payroll.hr_payroll_rules_mi_inc_withhold': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_mi_sit',

    'l10n_us_mn_hr_payrol.res_partner_mn_ui_unemp': 'l10n_us_hr_payroll.res_partner_us_mn_dor',
    'l10n_us_mn_hr_payrol.res_partner_mn_dor_withhold': 'l10n_us_hr_payroll.res_partner_us_mn_dor_sit',
    'l10n_us_mn_hr_payrol.contrib_register_mn_ui_unemp': 'l10n_us_hr_payroll.contrib_register_us_mn_dor',
    'l10n_us_mn_hr_payrol.contrib_register_mn_dor_withhold': 'l10n_us_hr_payroll.contrib_register_us_mn_dor_sit',
    'l10n_us_mn_hr_payrol.hr_payroll_rules_mn_unemp': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_mn_suta',
    'l10n_us_mn_hr_payrol.hr_payroll_rules_mn_inc_withhold': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_mn_sit',

    'l10n_us_mo_hr_payroll.res_partner_modor_unemp': 'l10n_us_hr_payroll.res_partner_us_mo_dor',
    'l10n_us_mo_hr_payroll.res_partner_modor_withhold': 'l10n_us_hr_payroll.res_partner_us_mo_dor_sit',
    'l10n_us_mo_hr_payroll.contrib_register_modor_unemp': 'l10n_us_hr_payroll.contrib_register_us_mo_dor',
    'l10n_us_mo_hr_payroll.contrib_register_modor_withhold': 'l10n_us_hr_payroll.contrib_register_us_mo_dor_sit',
    'l10n_us_mo_hr_payroll.hr_payroll_rules_mo_unemp_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_mo_suta',
    'l10n_us_mo_hr_payroll.hr_payroll_rules_mo_inc_withhold_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_mo_sit',

    'l10n_us_ms_hr_payroll.res_partner_msdor_unemp': 'l10n_us_hr_payroll.res_partner_us_ms_dor',
    'l10n_us_ms_hr_payroll.res_partner_msdor_withhold': 'l10n_us_hr_payroll.res_partner_us_ms_dor_sit',
    'l10n_us_ms_hr_payroll.contrib_register_msdor_unemp': 'l10n_us_hr_payroll.contrib_register_us_ms_dor',
    'l10n_us_ms_hr_payroll.contrib_register_msdor_withhold': 'l10n_us_hr_payroll.contrib_register_us_ms_dor_sit',
    'l10n_us_ms_hr_payroll.hr_payroll_rules_ms_unemp': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_ms_suta',
    'l10n_us_ms_hr_payroll.hr_payroll_rules_ms_inc_withhold': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_ms_sit',

    'l10n_us_mt_hr_payroll.res_partner_mtdor_unemp': 'l10n_us_hr_payroll.res_partner_us_mt_dor',
    'l10n_us_mt_hr_payroll.res_partner_mtdor_withhold': 'l10n_us_hr_payroll.res_partner_us_mt_dor_sit',
    'l10n_us_mt_hr_payroll.contrib_register_mtdor_unemp': 'l10n_us_hr_payroll.contrib_register_us_mt_dor',
    'l10n_us_mt_hr_payroll.contrib_register_mtdor_withhold': 'l10n_us_hr_payroll.contrib_register_us_mt_dor_sit',
    'l10n_us_mt_hr_payroll.hr_payroll_rules_mt_unemp': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_mt_suta',
    'l10n_us_mt_hr_payroll.hr_payroll_rules_mt_inc_withhold': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_mt_sit',

    'l10n_us_nc_hr_payroll.res_partner_ncdor_unemp':'l10n_us_hr_payroll.res_partner_us_nc_dor',
    'l10n_us_nc_hr_payroll.res_partner_ncdor_withhold': 'l10n_us_hr_payroll.res_partner_us_nc_dor_sit',
    'l10n_us_nc_hr_payroll.contrib_register_ncdor_unemp': 'l10n_us_hr_payroll.contrib_register_us_nc_dor',
    'l10n_us_nc_hr_payroll.contrib_register_ncdor_withhold': 'l10n_us_hr_payroll.contrib_register_us_nc_dor_sit',
    'l10n_us_nc_hr_payroll.hr_payroll_rules_nc_unemp_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_nc_suta',
    'l10n_us_nc_hr_payroll.hr_payroll_rules_nc_inc_withhold_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_nc_sit',

    'l10n_us_nj_hr_payroll.res_partner_njdor_unemp_employee': 'l10n_us_hr_payroll.res_partner_us_nj_dor',
    'l10n_us_nj_hr_payroll.res_partner_njdor_withhold': 'l10n_us_hr_payroll.res_partner_us_nj_dor_sit',
    'l10n_us_nj_hr_payroll.contrib_register_njdor_unemp_employee': 'l10n_us_hr_payroll.contrib_register_us_nj_dor',
    'l10n_us_nj_hr_payroll.contrib_register_njdor_withhold': 'l10n_us_hr_payroll.contrib_register_us_nj_dor_sit',
    'l10n_us_nj_hr_payroll.hr_payroll_rules_nj_unemp_employee_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_nj_suta',
    'l10n_us_nj_hr_payroll.hr_payroll_rules_nj_unemp_company_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_nj_suta',
    'l10n_us_nj_hr_payroll.hr_payroll_rules_nj_sdi_employee_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_nj_sdi',
    'l10n_us_nj_hr_payroll.hr_payroll_rules_nj_sdi_company_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_nj_sdi',
    'l10n_us_nj_hr_payroll.hr_payroll_rules_nj_fli_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_nj_fli',
    'l10n_us_nj_hr_payroll.hr_payroll_rules_nj_wf_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_nj_wf',
    'l10n_us_nj_hr_payroll.hr_payroll_rules_nj_wf_er': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_nj_wf',
    'l10n_us_nj_hr_payroll.hr_payroll_rules_nj_inc_withhold_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_nj_sit',

    'l10n_us_oh_hr_payroll.res_partner_ohdor_unemp': 'l10n_us_hr_payroll.res_partner_us_oh_dor',
    'l10n_us_oh_hr_payroll.res_partner_ohdor_withhold': 'l10n_us_hr_payroll.res_partner_us_oh_dor_sit',
    'l10n_us_oh_hr_payroll.res_partner_ohdor_unemp': 'l10n_us_hr_payroll.res_partner_us_oh_dor',
    'l10n_us_oh_hr_payroll.res_partner_ohdor_withhold': 'l10n_us_hr_payroll.res_partner_us_oh_dor_sit',
    'l10n_us_oh_hr_payroll.hr_payroll_rules_oh_unemp_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_oh_suta',
    'l10n_us_oh_hr_payroll.hr_payroll_rules_oh_inc_withhold_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_oh_sit',

    'l10n_us_pa_hr_payroll.res_partner_pador_unemp_company': 'l10n_us_hr_payroll.res_partner_us_pa_dor',
    'l10n_us_pa_hr_payroll.res_partner_pador_withhold': 'l10n_us_hr_payroll.res_partner_us_pa_dor_sit',
    'l10n_us_pa_hr_payroll.contrib_register_pador_unemp_company': 'l10n_us_hr_payroll.contrib_register_us_pa_dor',
    'l10n_us_pa_hr_payroll.contrib_register_pador_withhold': 'l10n_us_hr_payroll.contrib_register_us_pa_dor_sit',
    'l10n_us_pa_hr_payroll.hr_payroll_rules_pa_unemp_employee_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_pa_suta',
    'l10n_us_pa_hr_payroll.hr_payroll_rules_pa_unemp_company_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_pa_suta',
    'l10n_us_pa_hr_payroll.hr_payroll_rules_pa_inc_withhold_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_pa_sit',

    'l10n_us_sc_hr_payroll.res_partner_sc_dew_unemp': 'l10n_us_hr.payroll.res_partner_us_sc_dor',
    'l10n_us_sc_hr_payroll.res_partner_sc_dor_withhold': 'l10n_us_hr.payroll.res_partner_us_sc_dor_sit',
    'l10n_us_sc_hr_payroll.contrib_register_sc_dew_unemp': 'l10n_us_hr.payroll.contrib_register_us_sc_dor',
    'l10n_us_sc_hr_payroll.contrib_register_sc_dor_withhold': 'l10n_us_hr.payroll.contrib_register_us_sc_dor_sit',
    'l10n_us_sc_hr_payroll.hr_payroll_rules_sc_unemp': 'l10n_us_hr.payroll.hr_payroll_rule_er_us_sc_suta',
    'l10n_us_sc_hr_payroll.hr_payroll_rules_sc_inc_withhold': 'l10n_us_hr.payroll.hr_payroll_rule_ee_us_sc_sit',

    'l10n_us_tx_hr_payroll.res_partner_txdor': 'l10n_us_hr_payroll.res_partner_us_tx_dor',
    'l10n_us_tx_hr_payroll.contrib_register_txdor': 'l10n_us_hr_payroll.contrib_register_us_tx_dor',
    'l10n_us_tx_hr_payroll.hr_payroll_rules_tx_unemp_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_tx_suta',
    'l10n_us_tx_hr_payroll.hr_payroll_rules_tx_oa_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_tx_suta_oa',
    'l10n_us_tx_hr_payroll.hr_payroll_rules_tx_etia_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_tx_suta_etia',

    'l10n_us_va_hr_payroll.res_partner_vador_unemp': 'l10n_us_hr_payroll.res_partner_us_va_dor',
    'l10n_us_va_hr_payroll.res_partner_vador_withhold': 'l10n_us_hr_payroll.res_partner_us_va_dor_sit',
    'l10n_us_va_hr_payroll.contrib_register_vador_unemp': 'l10n_us_hr_payroll.contrib_register_us_va_dor',
    'l10n_us_va_hr_payroll.contrib_register_vador_withhold': 'l10n_us_hr_payroll.contrib_register_us_va_dor_sit',
    'l10n_us_va_hr_payroll.hr_payroll_rules_va_unemp_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_va_suta',
    'l10n_us_va_hr_payroll.hr_payroll_rules_va_inc_withhold_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_va_sit',

    'l10n_us_wa_hr_payroll.res_partner_wador_unemp': 'l10n_us_hr_payroll.res_partner_us_wa_dor',
    'l10n_us_wa_hr_payroll.res_partner_wador_lni': 'l10n_us_hr_payroll.res_partner_us_wa_dor_lni',
    'l10n_us_wa_hr_payroll.contrib_register_wador_unemp': 'l10n_us_hr_payroll.contrib_register_us_wa_dor',
    'l10n_us_wa_hr_payroll.contrib_register_wador_lni': 'l10n_us_hr_payroll.contrib_register_us_wa_dor_lni',
    'l10n_us_wa_hr_payroll.hr_payroll_rules_wa_unemp_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_wa_suta',
    'l10n_us_wa_hr_payroll.hr_payroll_rules_wa_lni_withhold': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_wa_lni',
    'l10n_us_wa_hr_payroll.hr_payroll_rules_wa_lni': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_wa_lni',

    'l10n_us_wy_hr_payroll.res_partner_wy_dws_unemp': 'l10n_us_hr_payroll.res_partner_us_wy_dor',
    'l10n_us_wy_hr_payroll.contrib_register_wy_dws_unemp': 'l10n_us_hr_payroll.contrib_register_us_wy_dor',
    'l10n_us_wy_hr_payroll.hr_payroll_rules_wy_unemp': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_wy_suta',

}

XMLIDS_COPY_ACCOUNTING_2020 = {
    'l10n_us_hr_payroll.hr_payroll_rule_er_us_mt_suta': [
        'l10n_us_hr_payroll.hr_payroll_rule_er_us_mt_suta_aft',
    ],
    'l10n_us_hr_payroll.hr_payroll_rule_er_us_nj_wf': [
        'l10n_us_hr_payroll.hr_payroll_rule_er_us_nj_fli',
    ],
    'l10n_us_hr_payroll.hr_payroll_rule_er_us_wa_lni': [
        'l10n_us_hr_payroll.hr_payroll_rule_er_us_wa_fml',
    ],
    'l10n_us_hr_payroll.hr_payroll_rule_ee_us_wa_lni': [
        'l10n_us_hr_payroll.hr_payroll_rule_ee_us_wa_fml',
    ],
}
