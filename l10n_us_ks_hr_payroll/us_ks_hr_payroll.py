from odoo import models, fields, api


class USKSHrContract(models.Model):
    _inherit = 'hr.contract'

    ks_k4_allowances = fields.Integer(string="Kansas K-4 Allowances",
                                      default=0,
                                      help="Allowances claimed on K-4")
    ks_additional_withholding = fields.Float(string="Additional Withholding",
                                              default=0.0,
                                              help='Additional withholding from line 5 of form K-4')
    ks_k4_filing_status = fields.Selection([
        ('exempt', 'Exempt'),
        ('single', 'Single'),
        ('married', 'Married'),
        ('head_household', 'Head of Household')
    ], string='KS Filing Status', default='single')


    @api.multi
    def ks_unemp_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'ks_unemp_rate_' + str(year)):
            return self.employee_id.company_id['ks_unemp_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US Kansas.')


class KSCompany(models.Model):
    _inherit = 'res.company'

    ks_unemp_rate_2018 = fields.Float(string="Kansas Unemployment Insurance Rate 2018", default=2.7)
