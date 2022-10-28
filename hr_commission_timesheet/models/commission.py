# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class HrCommission(models.Model):
    _inherit = 'hr.commission'

    rate_type = fields.Selection(selection_add=[('timesheet', 'Timesheets')])

    @api.onchange('source_move_id', 'contract_id', 'rate_type', 'base_amount', 'rate')
    def _compute_amount(self):
        for commission in self.filtered(lambda c: c.rate_type == 'timesheet'):
            commission.rate = commission.contract_id.timesheet_commission_rate
        return super()._compute_amount()

    @api.model
    def invoice_validated(self, moves):
        source_moves = self._filter_source_moves_for_creation(moves)
        res = super().invoice_validated(moves)
        commission_obj = self.sudo()
        created_commissions = commission_obj.browse()
        for move in source_moves:
            timesheets = move.timesheet_ids
            employees = timesheets.mapped('employee_id')
            for employee in employees:
                contract = employee.contract_id
                move_amount = move.amount_for_commission()
                if all((contract, contract.timesheet_commission_rate)):
                    commission = commission_obj.create({
                        'employee_id': employee.id,
                        'contract_id': contract.id,
                        'source_move_id': move.id,
                        'base_amount': move_amount,
                        'rate_type': 'timesheet',
                        'company_id': move.company_id.id,
                    })
                    move.commission_ids += commission
                    created_commissions += commission

            if created_commissions and move.company_id.commission_type == 'on_invoice':
                created_commissions.sudo().action_confirm()

        return res
