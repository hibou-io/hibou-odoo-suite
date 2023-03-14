from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class HRExpense(models.Model):
    _inherit = 'hr.expense'

    vendor_id = fields.Many2one('res.partner', string='Vendor')

    def _get_account_move_line_values(self):
        self.ensure_one()
        expense = self
        return {
            'name': expense.employee_id.name + ': ' + expense.name.split('\n')[0][:64],
            'account_id': expense.account_id.id,
            'quantity': expense.quantity or 1,
            'price_unit': expense.unit_amount if expense.unit_amount != 0 else expense.total_amount,
            'product_id': expense.product_id.id,
            'product_uom_id': expense.product_uom_id.id,
            'analytic_distribution': expense.analytic_distribution,
            'expense_id': expense.id,
            'partner_id': expense.vendor_id.id,
            'tax_ids': [(6, 0, expense.tax_ids.ids)],
            'currency_id': expense.currency_id.id,
        }
    
    def action_move_create(self):
        """
        Move creation value are no longer built in extendable methods,
        so we need to override here to edit moves before they are posted
        """
        company_paid = self.filtered(lambda e: e.payment_mode == 'company_account')
        if company_paid.filtered(lambda e: not e.vendor_id):
            raise UserError(_('You must have an assigned vendor to process a Company Paid Expense'))
        moves_by_expense = super(HRExpense, self - company_paid).action_move_create()
        company_moves = self.env['account.move'].create(company_paid.sheet_id._prepare_account_move_vals_list())
        company_moves._post()

        for expense in company_paid:
            expense.sheet_id.paid_expense_sheets()

        moves_by_expense.update({move.expense_sheet_id.id: move for move in company_moves})
        return moves_by_expense


class HRExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    expense_line_ids = fields.One2many(states={'done': [('readonly', True)], 'post': [('readonly', True)]})
    
    def _prepare_account_move_vals_list(self):
        if self.filtered(lambda s: len(s.expense_line_ids.vendor_id) > 1):
            raise UserError(_("You cannot create journal entries for different vendors in the same report."))
        return [{
            'journal_id': (
                sheet.bank_journal_id
                if sheet.payment_mode == 'company_account' else
                sheet.journal_id
            ).id,
            'move_type': 'in_receipt',
            'company_id': sheet.company_id.id,
            'partner_id': sheet.expense_line_ids.vendor_id.id,
            'date': sheet.accounting_date or fields.Date.context_today(sheet),
            'invoice_date': sheet.accounting_date or fields.Date.context_today(sheet),
            'ref': sheet.name,
            # force the name to the default value, to avoid an eventual 'default_name' in the context
            # to set it to '' which cause no number to be given to the account.move when posted.
            'name': '/',
            'expense_sheet_id': [fields.Command.set(sheet.ids)],
            'line_ids':[
                fields.Command.create(expense._get_account_move_line_values())
                for expense in sheet.expense_line_ids
            ]
        } for sheet in self]
