from odoo import api,fields,models


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    contract_wc_code_id = fields.Many2one('hr.wc_code', string='Workers Comp. Code',
                                          related='contract_id.wc_code_id', store=True)
