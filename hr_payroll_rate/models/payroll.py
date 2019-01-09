from odoo import api, fields, models


class PayrollRate(models.Model):
    _name = 'hr.payroll.rate'
    _description = 'Payroll Rate'

    active = fields.Boolean(string='Active', default=True)
    name = fields.Char(string='Name')
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To')
    company_id = fields.Many2one('res.company', string='Company', copy=False,
                                 default=False)
    rate = fields.Float(string='Rate', required=True)
    code = fields.Char(string='Code', required=True)

    limit_payslip = fields.Float(string='Payslip Limit')
    limit_year = fields.Float(string='Year Limit')
    wage_limit_payslip = fields.Float(string='Payslip Wage Limit')
    wage_limit_year = fields.Float(string='Year Wage Limit')


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    def _get_rate_domain(self, code):
        return [
            '|', ('date_to', '=', False), ('date_to', '>=', self.date_to),
            '|', ('company_id', '=', False), ('company_id', '=', self.company_id.id),
            ('code', '=', code),
            ('date_from', '<=', self.date_from),
        ]

    def get_rate(self, code):
        self.ensure_one()
        return self.env['hr.payroll.rate'].search(
            self._get_rate_domain(code), limit=1, order='date_from DESC, company_id ASC')
