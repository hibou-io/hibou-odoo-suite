from odoo import models, fields, api


class USPAHrContract(models.Model):
    _inherit = 'hr.contract'

    pa_additional_withholding = fields.Integer(string="Additional Withholding",
                                               default=0)

    @api.multi
    def pa_unemp_company_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'pa_unemp_company_rate_' + str(year)):
            return self.employee_id.company_id['pa_unemp_company_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US Pennsylvania')

    def pa_unemp_employee_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'pa_unemp_employee_rate_' + str(year)):
            return self.employee_id.company_id['pa_unemp_employee_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US Pennsylvania')

    def pa_withhold_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'pa_withhold_rate_' + str(year)):
            return self.employee_id.company_id['pa_withhold_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US Pennsylvania')


class PACompany(models.Model):
    _inherit = 'res.company'

    # Company Unemployment rate is default rate for new employers.
    pa_unemp_company_rate_2018 = fields.Float(string="Pennsylvania Unemployment Rate 2018", default=3.6890)
    pa_unemp_employee_rate_2018 = fields.Float(string="Pennsylvania Unemployment Rate 2018", default=0.06)
    pa_withhold_rate_2018 = fields.Float(string="Pennsylvania Income Tax Rate 2018", default=3.07)

