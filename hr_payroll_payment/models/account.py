# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    payroll_entry_type = fields.Selection([
        ('original', 'Original'),
        ('grouped', 'Grouped'),
        ('slip', 'Payslip'),
    ], string='Payroll Entry Type',
        default='grouped',
        help="Grouped and Payslip will add partner info and group by account and partner. "
             "Payslip will generate a journal entry for every payslip.")
    payroll_payment_journal_id = fields.Many2one('account.journal', string='Payroll Payment Journal')
    payroll_payment_method_id = fields.Many2one('account.payment.method', string='Payroll Payment Method')
    payroll_payment_method_refund_id = fields.Many2one('account.payment.method', string='Payroll Refund Method')
