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
from .state.ca_california import ca_california_state_income_withholding
from .state.co_colorado import co_colorado_state_income_withholding
from .state.ct_connecticut import ct_connecticut_state_income_withholding
from .state.de_delaware import de_delaware_state_income_withholding
from .state.ga_georgia import ga_georgia_state_income_withholding
from .state.hi_hawaii import hi_hawaii_state_income_withholding
from .state.ia_iowa import ia_iowa_state_income_withholding
from .state.id_idaho import id_idaho_state_income_withholding
from .state.il_illinois import il_illinois_state_income_withholding
from .state.in_indiana import in_indiana_state_income_withholding
from .state.ks_kansas import ks_kansas_state_income_withholding
from .state.ky_kentucky import ky_kentucky_state_income_withholding
from .state.la_louisiana import la_louisiana_state_income_withholding
from .state.me_maine import me_maine_state_income_withholding
from .state.mi_michigan import mi_michigan_state_income_withholding
from .state.mn_minnesota import mn_minnesota_state_income_withholding
from .state.mo_missouri import mo_missouri_state_income_withholding
from .state.ms_mississippi import ms_mississippi_state_income_withholding
from .state.mt_montana import mt_montana_state_income_withholding
from .state.nc_northcarolina import nc_northcarolina_state_income_withholding
from .state.nd_north_dakota import nd_north_dakota_state_income_withholding
from .state.ne_nebraska import ne_nebraska_state_income_withholding
from .state.nj_newjersey import nj_newjersey_state_income_withholding
from .state.nm_new_mexico import nm_new_mexico_state_income_withholding
from .state.ny_new_york import ny_new_york_state_income_withholding
from .state.oh_ohio import oh_ohio_state_income_withholding
from .state.ok_oklahoma import ok_oklahoma_state_income_withholding
from .state.ri_rhode_island import ri_rhode_island_state_income_withholding
from .state.sc_south_carolina import sc_south_carolina_state_income_withholding
from .state.ut_utah import ut_utah_state_income_withholding
from .state.vt_vermont import vt_vermont_state_income_withholding
from .state.va_virginia import va_virginia_state_income_withholding
from .state.wa_washington import wa_washington_fml_er, \
                                 wa_washington_fml_ee
from .state.wi_wisconsin import wi_wisconsin_state_income_withholding
from .state.wv_west_virginia import wv_west_virginia_state_income_withholding


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
            'ca_california_state_income_withholding': ca_california_state_income_withholding,
            'co_colorado_state_income_withholding': co_colorado_state_income_withholding,
            'ct_connecticut_state_income_withholding': ct_connecticut_state_income_withholding,
            'de_delaware_state_income_withholding': de_delaware_state_income_withholding,
            'ga_georgia_state_income_withholding': ga_georgia_state_income_withholding,
            'hi_hawaii_state_income_withholding': hi_hawaii_state_income_withholding,
            'ia_iowa_state_income_withholding': ia_iowa_state_income_withholding,
            'id_idaho_state_income_withholding': id_idaho_state_income_withholding,
            'il_illinois_state_income_withholding': il_illinois_state_income_withholding,
            'in_indiana_state_income_withholding': in_indiana_state_income_withholding,
            'ks_kansas_state_income_withholding': ks_kansas_state_income_withholding,
            'ky_kentucky_state_income_withholding':ky_kentucky_state_income_withholding,
            'la_louisiana_state_income_withholding': la_louisiana_state_income_withholding,
            'me_maine_state_income_withholding': me_maine_state_income_withholding,
            'mi_michigan_state_income_withholding': mi_michigan_state_income_withholding,
            'mn_minnesota_state_income_withholding': mn_minnesota_state_income_withholding,
            'mo_missouri_state_income_withholding': mo_missouri_state_income_withholding,
            'ms_mississippi_state_income_withholding': ms_mississippi_state_income_withholding,
            'mt_montana_state_income_withholding': mt_montana_state_income_withholding,
            'nc_northcarolina_state_income_withholding': nc_northcarolina_state_income_withholding,
            'nd_north_dakota_state_income_withholding': nd_north_dakota_state_income_withholding,
            'ne_nebraska_state_income_withholding': ne_nebraska_state_income_withholding,
            'nj_newjersey_state_income_withholding': nj_newjersey_state_income_withholding,
            'nm_new_mexico_state_income_withholding': nm_new_mexico_state_income_withholding,
            'ny_new_york_state_income_withholding': ny_new_york_state_income_withholding,
            'oh_ohio_state_income_withholding': oh_ohio_state_income_withholding,
            'ok_oklahoma_state_income_withholding': ok_oklahoma_state_income_withholding,
            'ri_rhode_island_state_income_withholding': ri_rhode_island_state_income_withholding,
            'sc_south_carolina_state_income_withholding': sc_south_carolina_state_income_withholding,
            'ut_utah_state_income_withholding': ut_utah_state_income_withholding,
            'vt_vermont_state_income_withholding': vt_vermont_state_income_withholding,
            'va_virginia_state_income_withholding': va_virginia_state_income_withholding,
            'wa_washington_fml_er': wa_washington_fml_er,
            'wa_washington_fml_ee': wa_washington_fml_ee,
            'wi_wisconsin_state_income_withholding': wi_wisconsin_state_income_withholding,
            'wv_west_virginia_state_income_withholding': wv_west_virginia_state_income_withholding,
        })
        return res

    def get_year(self):
        # Helper method to get the year (normalized between Odoo Versions)
        return self.date_to.year

    def get_pay_periods_in_year(self):
        return self.PAY_PERIODS_IN_YEAR.get(self.contract_id.schedule_pay, 0)
