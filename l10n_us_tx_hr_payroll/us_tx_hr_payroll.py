from odoo import models, fields, api


class USTXHrContract(models.Model):
    _inherit = 'hr.contract'

    @api.multi
    def tx_unemp_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'tx_unemp_rate_' + str(year)):
            return self.employee_id.company_id['tx_unemp_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US Texas.')

    def tx_oa_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'tx_oa_rate_' + str(year)):
            return self.employee_id.company_id['tx_oa_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US Texas.')

    def tx_etia_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'tx_etia_rate_' + str(year)):
            return self.employee_id.company_id['tx_etia_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US Texas.')


class TXCompany(models.Model):
    _inherit = 'res.company'

    tx_unemp_rate_2018 = fields.Float(string="Texas Unemployment Rate 2018", default=2.7)
    tx_oa_rate_2018 = fields.Float(strimg="Texas Obligation Assessment Rate 2018", default=0.0)
    tx_etia_rate_2018 = fields.Float(string="Texas Employment & Training Investment Assessment Rate", default=0.1)
