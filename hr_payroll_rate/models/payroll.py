import ast
from odoo import api, fields, models
from odoo.tools import ormcache
from odoo.exceptions import UserError


class PayrollRate(models.Model):
    _name = 'hr.payroll.rate'
    _description = 'Payroll Rate'
    _order = 'date_from DESC, company_id ASC'

    active = fields.Boolean(string='Active', default=True)
    name = fields.Char(string='Name')
    date_from = fields.Date(string='Date From', index=True, required=True)
    date_to = fields.Date(string='Date To')
    company_id = fields.Many2one('res.company', string='Company', copy=False,
                                 default=False)
    rate = fields.Float(string='Rate', digits=(12, 6), default=0.0, required=True)
    code = fields.Char(string='Code', index=True, required=True)

    limit_payslip = fields.Float(string='Payslip Limit')
    limit_year = fields.Float(string='Year Limit')
    wage_limit_payslip = fields.Float(string='Payslip Wage Limit')
    wage_limit_year = fields.Float(string='Year Wage Limit')
    parameter_value = fields.Text(help="Python data structure")

    @api.model
    @ormcache('code', 'date', 'company_id', 'self.env.user.company_id.id')
    def _get_parameter_from_code(self, code, company_id, date=None):
        if not date:
            date = fields.Date.today()
        rate = self.search([
            ('code', '=', code),
            ('date_from', '<=', date),
        ], limit=1)
        if not rate:
            raise UserError(_("No rule parameter with code '%s' was found for %s ") % (code, date))
        return ast.literal_eval(rate.parameter_value)


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

    def rule_parameter(self, code):
        return self.env['hr.payroll.rate']._get_parameter_from_code(code, self.company_id.id, self.date_to)
