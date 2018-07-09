from odoo import models, fields, api


class USCAHrContract(models.Model):
    _inherit = 'hr.contract'

    ca_de4_allowances = fields.Integer(string="California CA-4 Allowances",
                                       default=0,
                                       help="Estimated Deductions claimed on DE-4")
    ca_additional_allowances = fields.Integer(string="Additional Allowances", default=0)
    ca_de4_filing_status = fields.Selection([
        ('exempt', 'Exempt'),
        ('single', 'Single'),
        ('married', 'Married'),
        ('head_household', 'Head of Household')
    ], string='CA Filing Status', default='single')

    @api.multi
    def ca_uit_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'ca_uit_rate_' + str(year)):
            return self.employee_id.company_id['ca_uit_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US California.')

    def ca_ett_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'ca_ett_rate_' + str(year)):
            return self.employee_id.company_id['ca_ett_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US California.')

    def ca_sdi_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'ca_sdi_rate_' + str(year)):
            return self.employee_id.company_id['ca_sdi_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US California.')


class CACompany(models.Model):
    _inherit = 'res.company'

    # UIT can be calculated using http://www.edd.ca.gov/pdf_pub_ctr/de44.pdf ETT is default.
    ca_uit_rate_2018 = fields.Float(string="California Unemployment Insurance Tax Rate 2018", default=2.6)
    ca_ett_rate_2018 = fields.Float(string="California Employment Training Tax Rate 2018", default=0.1)
    ca_sdi_rate_2018 = fields.Float(string="California State Disability Insurance Rate 2018", default=1.0)
