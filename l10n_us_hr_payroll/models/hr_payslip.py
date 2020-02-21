# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models

from .federal.fed_940 import er_us_940_futa
from .federal.fed_941 import ee_us_941_fica_ss, \
                             ee_us_941_fica_m, \
                             ee_us_941_fica_m_add,\
                             er_us_941_fica_ss, \
                             er_us_941_fica_m, \
                             ee_us_941_fit
from .state.general import general_state_unemployment, \
                           general_state_income_withholding, \
                           is_us_state
from .state.al_alabama import al_alabama_state_income_withholding
from .state.ar_arkansas import ar_arkansas_state_income_withholding
from .state.az_arizona import az_arizona_state_income_withholding
from .state.ct_connecticut import ct_connecticut_state_income_withholding
from .state.ga_georgia import ga_georgia_state_income_withholding
from .state.il_illinois import il_illinois_state_income_withholding
from .state.mi_michigan import mi_michigan_state_income_withholding
from .state.mn_minnesota import mn_minnesota_state_income_withholding
from .state.mo_missouri import mo_missouri_state_income_withholding
from .state.ms_mississippi import ms_mississippi_state_income_withholding
from .state.mt_montana import mt_montana_state_income_withholding
from .state.nc_northcarolina import nc_northcarolina_state_income_withholding
from .state.nj_newjersey import nj_newjersey_state_income_withholding
from .state.oh_ohio import oh_ohio_state_income_withholding
from .state.va_virginia import va_virginia_state_income_withholding
from .state.wa_washington import wa_washington_fml_er, \
                                 wa_washington_fml_ee


class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    # From IRS Publication 15-T or logically (annually, bi-monthly)
    PAY_PERIODS_IN_YEAR = {
            'annually':        1,
            'semi-annually':   2,
            'quarterly':       4,
            'bi-monthly':      6,
            'monthly':        12,
            'semi-monthly':   24,
            'bi-weekly':      26,
            'weekly':         52,
            'daily':         260,
        }

    def _get_base_local_dict(self):
        res = super()._get_base_local_dict()
        res.update({
            'er_us_940_futa': er_us_940_futa,
            'ee_us_941_fica_ss': ee_us_941_fica_ss,
            'ee_us_941_fica_m': ee_us_941_fica_m,
            'ee_us_941_fica_m_add': ee_us_941_fica_m_add,
            'er_us_941_fica_ss': er_us_941_fica_ss,
            'er_us_941_fica_m': er_us_941_fica_m,
            'ee_us_941_fit': ee_us_941_fit,
            'general_state_unemployment': general_state_unemployment,
            'general_state_income_withholding': general_state_income_withholding,
            'is_us_state': is_us_state,
            'al_alabama_state_income_withholding': al_alabama_state_income_withholding,
            'ar_arkansas_state_income_withholding': ar_arkansas_state_income_withholding,
            'az_arizona_state_income_withholding': az_arizona_state_income_withholding,
            'ct_connecticut_state_income_withholding': ct_connecticut_state_income_withholding,
            'ga_georgia_state_income_withholding': ga_georgia_state_income_withholding,
            'il_illinois_state_income_withholding': il_illinois_state_income_withholding,
            'mi_michigan_state_income_withholding': mi_michigan_state_income_withholding,
            'mn_minnesota_state_income_withholding': mn_minnesota_state_income_withholding,
            'mo_missouri_state_income_withholding': mo_missouri_state_income_withholding,
            'ms_mississippi_state_income_withholding': ms_mississippi_state_income_withholding,
            'mt_montana_state_income_withholding': mt_montana_state_income_withholding,
            'nc_northcarolina_state_income_withholding': nc_northcarolina_state_income_withholding,
            'nj_newjersey_state_income_withholding': nj_newjersey_state_income_withholding,
            'oh_ohio_state_income_withholding': oh_ohio_state_income_withholding,
            'va_virginia_state_income_withholding': va_virginia_state_income_withholding,
            'wa_washington_fml_er': wa_washington_fml_er,
            'wa_washington_fml_ee': wa_washington_fml_ee,
        })
        return res

    def get_year(self):
        # Helper method to get the year (normalized between Odoo Versions)
        return self.date_to.year

    def get_pay_periods_in_year(self):
        return self.PAY_PERIODS_IN_YEAR.get(self.contract_id.schedule_pay, 0)
