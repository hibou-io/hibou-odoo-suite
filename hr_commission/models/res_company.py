# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    commission_journal_id = fields.Many2one('account.journal', string='Commission Journal')
    commission_liability_id = fields.Many2one('account.account', string='Commission Liability Account')
    commission_type = fields.Selection([
        ('on_invoice', 'On Invoice Validation'),
        ('on_invoice_paid', 'On Invoice Paid'),
    ], string='Pay Commission', default='on_invoice_paid')
    commission_amount_type = fields.Selection([
        ('on_invoice_margin', 'On Invoice Margin'),
        ('on_invoice_total', 'On Invoice Total'),
        ('on_invoice_untaxed', 'On Invoice Total Tax Excluded'),
    ], string='Commission Base', default='on_invoice_margin')
