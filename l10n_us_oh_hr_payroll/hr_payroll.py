from odoo import models, fields, api


class USOHHrContract(models.Model):
    _inherit = 'hr.contract'

    oh_income_allowances = fields.Integer(string='Ohio Income Allowances', default=0)
    oh_additional_withholding = fields.Float(string="Additional Withholding", default=0.0)

    @api.multi
    def oh_unemp_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'oh_unemp_rate_' + str(year)):
            return self.employee_id.company_id['oh_unemp_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US Ohio.')


class OHCompany(models.Model):
    _inherit = 'res.company'

    # Defaults from :: https://jfs.ohio.gov/ouc/uctax/rates.stm
    oh_unemp_rate_2016 = fields.Float(string="Ohio Unemployment Rate 2016", default=2.7)
    oh_unemp_rate_2017 = fields.Float(string="Ohio Unemployment Rate 2017", default=2.7)
    oh_unemp_rate_2018 = fields.Float(string="Ohio Unemployment Rate 2018", default=2.7)
