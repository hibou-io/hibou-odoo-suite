from odoo import models, fields, api


class USNYHrContract(models.Model):
    _inherit = 'hr.contract'

    ny_it2104_allowances = fields.Integer(string="New York IT-2104 Allowances",
                                       default=0,
                                       help="Allowances claimed on line 1 of IT-2104")
    ny_additional_withholding = fields.Integer(string="Additional Withholding",
                                               default=0,
                                               help="Line 3 of IT-2104")
    ny_it2104_filing_status = fields.Selection([
        ('exempt', 'Exempt'),
        ('single', 'Single'),
        ('married', 'Married'),
    ], string='NY Filing Status', default='single')

    @api.multi
    def ny_unemp_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'ny_unemp_rate_' + str(year)):
            return self.employee_id.company_id['ny_unemp_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US New York.')

    def ny_rsf_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'ny_rsf_rate_' + str(year)):
            return self.employee_id.company_id['ny_rsf_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US New York.')

    def ny_mctmt_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'ny_mctmt_rate_' + str(year)):
            return self.employee_id.company_id['ny_mctmt_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US New York.')


class NYCompany(models.Model):
    _inherit = 'res.company'

    # Unemployment Rate is default for New Employer.
    ny_unemp_rate_2018 = fields.Float(string="New York Unemployment Insurance Tax Rate 2018", default=3.925)
    ny_rsf_rate_2018 = fields.Float(string="New York Re-employment Service Fund Rate 2018", default=0.075)
    ny_mctmt_rate_2018 = fields.Float(string="New York Metropolitan Commuter Transportation Mobility Tax Rate 2018", default=0.0)
