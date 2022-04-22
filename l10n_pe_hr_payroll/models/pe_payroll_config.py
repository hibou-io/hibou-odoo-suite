# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class HRContractPEPayrollConfig(models.Model):
    _name = 'hr.contract.pe_payroll_config'
    _description = 'Contract PE Payroll Forms'

    name = fields.Char(string="Description")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    
    retirement_type = fields.Selection([
        ('afp', 'AFP'),
        ('onp', 'ONP'),
        ('retired', 'Retired'),
    ], string='Retirement Type', required=True, default='afp')
    
    onp_rule_id = fields.Many2one('hr.salary.rule', string='ONP Rule', domain=[('code', '=like', 'EE_PE_ONP%')])
    
    # AFP Type may actually be company specific....
    afp_type = fields.Selection([
        ('habitat', 'Habitat'),
        ('integra', 'Integra'),
        ('prima', 'Prima'),
        ('profuturo', 'Profuturo'),
    ], string='AFP Type', default='profuturo')
    afp_comision_type = fields.Selection([
        ('mixta', 'Mixta'),
        ('non_mixta', 'Non-Mixta'),
    ], string='AFP Commission Type', default='mixta')
    
    comp_ss_type = fields.Selection([
        ('essalud', 'Essalud'),
        ('eps', 'EPS'),
    ], string='Company Social Services', default='essalud')
    comp_ss_eps_rule_id = fields.Many2one('hr.salary.rule', string='Company Social Security EPS Rule')
    comp_life_insurance_rule_id = fields.Many2one('hr.salary.rule', string='Company Life Insurance Rule')
    comp_risk_insurance_rule_id = fields.Many2one('hr.salary.rule', string='Company Risk Insurance Rule')
