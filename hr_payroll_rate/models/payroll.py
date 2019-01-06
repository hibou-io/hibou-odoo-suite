from odoo import api, fields, models


class PayrollRate(models.Model):
    _name = 'hr.payroll.rate'
    _description = 'Payroll Rate'

    active = fields.Boolean(string='Active', default=True)
    name = fields.Char(string='Name')
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To')
    company_id = fields.Many2one('res.company', string='Company', copy=False,
                                 default=lambda self: self.env['res.company']._company_default_get())
    rate = fields.Float(string='Rate', required=True)
    code = fields.Char(string='Code', required=True)


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    def get_rate(self, code):
        self.ensure_one()
        return self.env['hr.payroll.rate'].search([
            '|', ('date_to', '=', False), ('date_to', '>=', self.date_to),
            ('code', '=', code),
            ('date_from', '<=', self.date_from),
        ], limit=1)
