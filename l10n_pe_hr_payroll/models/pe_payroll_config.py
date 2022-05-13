# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models, _


class HRContractPEPayrollConfig(models.Model):
    _name = 'hr.contract.pe_payroll_config'
    _description = 'Contract PE Payroll Forms'

    name = fields.Char(string="Description")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    date_hired = fields.Date(string='Date Hired', required=True, default=fields.Date.today,
                             help='For calculations like IR 5TH CAT.')
    
    ee_5ta_cat_exempt = fields.Boolean(string='Exempt from 5th Cat. withholding.')
    
    retirement_type = fields.Selection([
        ('afp', 'AFP'),
        ('onp', 'ONP'),
        ('retired', 'Retired'),
    ], string='Retirement Type', required=True, default='afp')
    
    # AFP Type may actually be company specific....
    afp_type = fields.Selection([
        ('habitat', 'Habitat'),
        ('integra', 'Integra'),
        ('prima', 'Prima'),
        ('profuturo', 'Profuturo'),
    ], string='AFP Type', default='profuturo')
    afp_comision_type = fields.Selection([
        ('mixta', 'Mixed'),
        ('non_mixta', 'Non-Mixed'),
    ], string='AFP Commission Type', default='mixta')
    
    comp_ss_type = fields.Selection([
        ('essalud', 'Essalud'),
        ('eps', 'EPS'),
    ], string='Company Social Services', default='essalud')
    comp_ss_eps_rule_id = fields.Many2one('hr.salary.rule', string='Company Social Security EPS Rule',
                                          domain=[('code', '=like', 'ER_PE_EPS%')],
                                          help="Rule code prefix 'ER_PE_EPS' to select here.")
