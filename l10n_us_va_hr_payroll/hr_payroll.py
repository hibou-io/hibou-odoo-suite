from openerp import models, fields, api


class USVAHrContract(models.Model):
    _inherit = 'hr.contract'

    va_va4_exemptions = fields.Integer(string='Virginia VA-4 Exemptions', default=0)
    va_va4p_exemptions = fields.Integer(string='Virginia VA-4P Exemptions', default=0)

    @api.multi
    def va_unemp_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'va_unemp_rate_' + str(year)):
            return self.employee_id.company_id['va_unemp_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US Virginia.')


class VACompany(models.Model):
    _inherit = 'res.company'

    # Defaults from :: https://www.payroll-taxes.com/state-tax/virginia
    va_unemp_rate_2018 = fields.Float(string="Virginia Unemployment Rate 2018", default=2.53)
