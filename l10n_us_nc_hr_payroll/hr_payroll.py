from odoo import models, fields, api


class USNCHrContract(models.Model):
    _inherit = 'hr.contract'

    nc_nc4_allowances = fields.Integer(string='North Carolina NC-4 Allowances', default=0)
    nc_nc4_filing_status = fields.Selection([
        ('exempt', 'Exempt'),
        ('single', 'Single'),
        ('married', 'Married'),
        ('surviving_spouse', 'Surviving Spouse'),
        ('head_household', 'Head of Household')
    ], string='NC Filing Status', default='single')
    nc_nc4_additional_wh = fields.Float(string="Additional Witholding", default=0.0,
                                        help="If you are filling out NC-4 NRA, this would be box 4; " \
                                             "otherwise box 2.")

    @api.multi
    def nc_unemp_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'nc_unemp_rate_' + str(year)):
            return self.employee_id.company_id['nc_unemp_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US North Carolina.')


class NCCompany(models.Model):
    _inherit = 'res.company'

    # Unemployment rate provided by Katherine
    nc_unemp_rate_2018 = fields.Float(string="North Carolina Unemployment Rate 2018", default=0.06)
