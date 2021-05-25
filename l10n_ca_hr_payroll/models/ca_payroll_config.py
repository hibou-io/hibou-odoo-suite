# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class HRContractCanadaPayrollConfig(models.Model):
    _name = 'hr.contract.ca_payroll_config'
    _description = 'Contract Canada Payroll Forms'

    # Quebec https://www.revenuquebec.ca/en/online-services/tools/webras-and-winras-calculation-of-source-deductions-and-employer-contributions/
    # https://www.canada.ca/en/revenue-agency/services/forms-publications/payroll/t4127-payroll-deductions-formulas/t4127-jan.html

    name = fields.Char(string="Description")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    state_id = fields.Many2one('res.country.state', string="Applied State")
    state_code = fields.Char(related='state_id.code')

    contributes_to_rpp = fields.Boolean(
        string='Employee Contributes to a registered pension plan (RPP)?',
        help='For tax deduction purposes, employers can deduct amounts contributed to an RPP, RRSP, PRPP, or RCA by or on behalf of an employee to determine the employee\'s taxable income',
        )
    rpp_withdrawal_per_check = fields.Float(
        string='RPP to Withdrawal Per Paycheck',
        help='Enter the dollar amount to be withdrawn per paycheck for a registered pension plan'
    )

    contributes_to_rrsp = fields.Boolean(
        string='Contributes to a registered retirement savings plan (RRSP)',
        help='For tax deduction purposes, employers can deduct amounts contributed to an RPP, RRSP, PRPP, or RCA by or on behalf of an employee to determine the employee\'s taxable income',
        )
    rrsp_withdrawal_per_check = fields.Float(
        string='RRSP to Withdrawal Per Paycheck',
        help='Enter the dollar amount to be withdrawn per paycheck for a registered retirement savings plan (RRSP)'
    )

    contributes_to_prpp = fields.Boolean(
        string='Contributes to a pooled registered pension plan (PRPP)?',
        help='For tax deduction purposes, employers can deduct amounts contributed to an RPP, RRSP, PRPP, or RCA by or on behalf of an employee to determine the employee\'s taxable income',
        )
    contributes_to_rca = fields.Boolean(
        string='Contributes to a retirement compensation arrangement (RCA)?',
        help='For tax deduction purposes, employers can deduct amounts contributed to an RPP, RRSP, PRPP, or RCA by or on behalf of an employee to determine the employee\'s taxable income',
        )
    alimony_or_maintenance_deduction_required = fields.Boolean(
        string='Alimony or maintenance payments required?',
        help='Annual deductions such as child care expenses and support payments, requested by an employee or pensioner and authorized by a tax services office or tax centre',
        )
    union_dues_deducted = fields.Boolean(
        string='Dues deducted?',
        help='Union dues for the pay period paid to a trade union, an association of public servants, or dues required under the law of a province to a parity or advisory committee or similar body',
        )
    lives_in_prescribed_zone = fields.Boolean(
        string='Perscribed zone deduction?',
        help='Annual deduction for living in a prescribed zone, as shown on Form TD1'
        )
    other_anual_deductions = fields.Boolean(
        string='Other annual deductions?',
        help='Annual deductions such as child care expenses and support payments, requested by an employee or pensioner and authorized by a tax services office or tax centre'
        )
    paid_commission = fields.Boolean(
        string='Paid a commission?',
        help='Does the employee receive any commissions?',
    )

    def ca_payroll_config_value(self, name):
        return self.ca_payroll_config_id[name]