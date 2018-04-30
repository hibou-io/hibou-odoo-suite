from odoo import models, fields, api


class USWAHrContract(models.Model):
    _inherit = 'hr.contract'

    wa_lni = fields.Many2one('hr.contract.lni.wa', string='WA State LNI')

    @api.multi
    def wa_unemp_rate(self, year):
        self.ensure_one()
        if self.futa_type == self.FUTA_TYPE_BASIC:
            return 0.0

        if hasattr(self.employee_id.company_id, 'wa_unemp_rate_' + str(year)):
            return self.employee_id.company_id['wa_unemp_rate_' + str(year)]

        raise NotImplemented('Year (' + str(year) + ') Not implemented for US Washington.')


class WACompany(models.Model):
    _inherit = 'res.company'

    # No Defaults, need to sign up with the Employment Security Department
    wa_unemp_rate_2018 = fields.Float(string="Washington Unemployment Rate 2018", default=0.0)


class WALNI(models.Model):
    _name = 'hr.contract.lni.wa'

    name = fields.Char(string='Name')
    rate = fields.Float(string='Rate (per hour worked)', digits=(7, 6))
    rate_emp_withhold = fields.Float(string='Employee Payroll Deduction Rate (per hour worked)', digits=(7, 6))
