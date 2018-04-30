from odoo import models, fields, api


class USMOHrContract(models.Model):
    _inherit = 'hr.contract'

    mo_mow4_filing_status = fields.Selection([
        ('', 'Exempt'),
        ('single', 'Single'),
        ('married', 'Married'),
        ('head_of_household', 'Head of Household'),
    ], string='Federal W4 Filing Status', default='single')
    mo_mow4_spouse_employed = fields.Boolean(string='Missouri W-4 Spouse Employed', default=False)
    mo_mow4_exemptions = fields.Integer(string='Missouri W-4 Exemptions', default=0)
    mo_mow4_additional_withholding = fields.Float(string="Missouri W-4 Additional Withholding", default=0.0)


    @api.multi
    def mo_unemp_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'mo_unemp_rate_' + str(year)):
            return self.employee_id.company_id['mo_unemp_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US Missouri.')


class MOCompany(models.Model):
    _inherit = 'res.company'

    # Defaults from :: https://labor.mo.gov/DES/Employers/tax_rates#beginning
    mo_unemp_rate_2018 = fields.Float(string="Missouri Unemployment Rate 2018", default=2.511)
