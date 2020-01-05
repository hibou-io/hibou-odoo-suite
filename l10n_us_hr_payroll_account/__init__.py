# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, SUPERUSER_ID
from . import models

def _post_install_hook_configure_journals(cr, registry):
    """
        This method will create a salary journal for each company and allocate it to each USA structure.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env['res.company'].search([('partner_id.country_id', '=', env.ref('base.us').id)])
    for company in companies:
        env['account.chart.template']._us_configure_payroll_account_data(company)
