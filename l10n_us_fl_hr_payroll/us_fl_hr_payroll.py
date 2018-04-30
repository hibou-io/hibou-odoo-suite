from openerp import models, fields, api


class USFLHrContract(models.Model):
    _inherit = 'hr.contract'

    @api.multi
    def fl_unemp_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'fl_unemp_rate_' + str(year)):
            return self.employee_id.company_id['fl_unemp_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US Florida.')


class FLCompany(models.Model):
    _inherit = 'res.company'

    # Defaults from :: http://floridarevenue.com/dor/taxes/reemployment.html
    fl_unemp_rate_2016 = fields.Float(string="Florida Unemployment Rate 2016", default=2.7)
    fl_unemp_rate_2017 = fields.Float(string="Florida Unemployment Rate 2017", default=2.7)
    fl_unemp_rate_2018 = fields.Float(string="Florida Unemployment Rate 2018", default=2.7)
