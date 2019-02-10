from odoo import models, fields, api


class USNCHrContract(models.Model):
    _inherit = 'hr.contract'

    nc_nc4_allowances = fields.Integer(string='North Carolina NC-4 Allowances', default=0)
    nc_nc4_filing_status = fields.Selection([
        ('exempt', 'Exempt'),
        ('single', 'Single'),
        ('married', 'Married'),
        ('surviving_spouse', 'Surviving Spouse'),
        ('head_household', 'Head of Household')
    ], string='NC Filing Status', default='single')
    nc_nc4_additional_wh = fields.Float(string="Additional Witholding", default=0.0,
                                        help="If you are filling out NC-4 NRA, this would be box 4; " \
                                             "otherwise box 2.")
