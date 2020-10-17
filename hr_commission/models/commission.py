# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools import float_is_zero
from odoo.exceptions import UserError


class Commission(models.Model):
    _name = 'hr.commission'
    _description = 'Commission'
    _order = 'id desc'

    state = fields.Selection([
        ('draft', 'New'),
        ('done', 'Confirmed'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),
        ], 'Status', default='draft')
    employee_id = fields.Many2one('hr.employee', required=1)
    user_id = fields.Many2one('res.users', related='employee_id.user_id')
    source_move_id = fields.Many2one('account.move')
    contract_id = fields.Many2one('hr.contract')
    structure_id = fields.Many2one('hr.commission.structure')
    rate_type = fields.Selection([
        ('normal', 'Normal'),
        ('structure', 'Structure'),
        ('admin', 'Admin'),
        ('manual', 'Manual'),
        ], 'Rate Type', default='normal')
    rate = fields.Float('Rate')
    base_total = fields.Float('Base Total')
    base_amount = fields.Float(string='Base Amount')
    amount = fields.Float(string='Amount')
    move_id = fields.Many2one('account.move', ondelete='set null')
    move_date = fields.Date(related='move_id.date', store=True)
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda s: s.env['res.company']._company_default_get('hr.commission'))
    memo = fields.Char(string='Memo')
    accounting_date = fields.Date('Force Accounting Date',
                                  help="Choose the accounting date at which you want to value the commission "
                                       "moves created by the commission instead of the default one.")
    payment_id = fields.Many2one('hr.commission.payment', string='Commission Payment', ondelete='set null')

    @api.depends('employee_id', 'source_move_id')
    def name_get(self):
        res = []
        for commission in self:
            name = ''
            if commission.source_move_id:
                name += commission.source_move_id.name
            if commission.employee_id:
                if name:
                    name += ' - ' + commission.employee_id.name
                else:
                    name += commission.employee_id.name
            res.append((commission.id, name))
        return res

    @api.onchange('rate_type')
    def _onchange_rate_type(self):
        for commission in self.filtered(lambda c: c.rate_type == 'manual'):
            commission.rate = 100.0

    @api.onchange('source_move_id', 'contract_id', 'rate_type', 'base_amount', 'rate')
    def _compute_amount(self):
        for commission in self:
            # Determine rate (if needed)
            if commission.structure_id and commission.rate_type == 'structure':
                line = commission.structure_id.line_ids.filtered(lambda l: l.employee_id == commission.employee_id)
                commission.rate = line.get_rate()
            elif commission.contract_id and commission.rate_type != 'manual':
                if commission.rate_type == 'normal':
                    commission.rate = commission.contract_id.commission_rate
                else:
                    commission.rate = commission.contract_id.admin_commission_rate

            rounding = 2
            if commission.source_move_id:
                rounding = commission.source_move_id.company_currency_id.rounding
                commission.base_total = commission.source_move_id.amount_total_signed
                commission.base_amount = commission.source_move_id.amount_for_commission()

            amount = (commission.base_amount * commission.rate) / 100.0
            if float_is_zero(amount, precision_rounding=rounding):
                amount = 0.0
            commission.amount = amount


    @api.model
    def create(self, values):
        res = super(Commission, self).create(values)
        res._compute_amount()
        if res.amount == 0.0 and res.state == 'draft':
            res.state = 'done'
        return res

    def unlink(self):
        if self.filtered(lambda c: c.move_id):
            raise UserError('You cannot delete a commission when it has an accounting entry.')
        return super(Commission, self).unlink()

    def _filter_source_moves_for_creation(self, moves):
        return moves.filtered(lambda i: i.user_id and not i.commission_ids)

    @api.model
    def _commissions_to_confirm(self, moves):
        commissions = moves.mapped('commission_ids')
        return commissions.filtered(lambda c: c.state != 'cancel' and not c.move_id)

    @api.model
    def invoice_validated(self, moves):
        employee_obj = self.env['hr.employee'].sudo()
        commission_obj = self.sudo()
        for move in self._filter_source_moves_for_creation(moves):
            move_amount = move.amount_for_commission()

            # Does the invoice have a commission structure?
            partner = move.partner_id
            commission_structure = partner.commission_structure_id
            while not commission_structure and partner:
                partner = partner.parent_id
                commission_structure = partner.commission_structure_id

            if commission_structure:
                commission_structure.create_for_source_move(move, move_amount)
            else:
                employee = employee_obj.search([('user_id', '=', move.user_id.id)], limit=1)
                contract = employee.contract_id
                if all((employee, contract)):
                    move.commission_ids += commission_obj.create({
                        'employee_id': employee.id,
                        'contract_id': contract.id,
                        'source_move_id': move.id,
                        'base_amount': move_amount,
                        'rate_type': 'normal',
                        'company_id': move.company_id.id,
                    })

                # Admin/Coach commission.
                employee = employee.coach_id
                contract = employee.contract_id
                if all((employee, contract)):
                    move.commission_ids += commission_obj.create({
                        'employee_id': employee.id,
                        'contract_id': contract.id,
                        'source_move_id': move.id,
                        'base_amount': move_amount,
                        'rate_type': 'admin',
                        'company_id': move.company_id.id,
                    })

            if move.commission_ids and move.company_id.commission_type == 'on_invoice':
                commissions = self._commissions_to_confirm(move)
                commissions.sudo().action_confirm()

        return True

    @api.model
    def invoice_paid(self, moves):
        commissions = self._commissions_to_confirm(moves)
        commissions.sudo().action_confirm()
        return True

    def action_confirm(self):
        move_obj = self.env['account.move'].sudo()

        for commission in self:
            if commission.state == 'cancel':
                continue
            if commission.move_id or commission.amount == 0.0:
                commission.write({'state': 'done'})
                continue

            journal = commission.company_id.commission_journal_id
            if not journal or not journal.default_debit_account_id or not journal.default_credit_account_id:
                raise UserError('Commission Journal not configured.')

            liability_account = commission.company_id.commission_liability_id
            if not liability_account:
                liability_account = commission.employee_id.address_home_id.property_account_payable_id
            if not liability_account:
                raise UserError('Commission liability account must be configured if employee\'s don\'t have AP setup.')

            date = commission.source_move_id.date if commission.source_move_id else fields.Date.context_today(commission)

            # Already paid.
            payments = commission.source_move_id._get_reconciled_payments()
            if payments:
                date = max(payments.mapped('payment_date'))
            if commission.accounting_date:
                date = commission.accounting_date

            ref = 'Commission for ' + commission.name_get()[0][1]
            if commission.memo:
                ref += ' :: ' + commission.memo

            move = move_obj.create({
                'date': date,
                'ref': ref,
                'journal_id': journal.id,
                'type': 'entry',
                'line_ids': [
                    (0, 0, {
                        'name': ref,
                        'partner_id': commission.employee_id.address_home_id.id,
                        'account_id': liability_account.id,
                        'credit': commission.amount if commission.amount > 0.0 else 0.0,
                        'debit': 0.0 if commission.amount > 0.0 else -commission.amount,
                    }),
                    (0, 0, {
                        'name': ref,
                        'partner_id': commission.employee_id.address_home_id.id,
                        'account_id': journal.default_credit_account_id.id if commission.amount > 0.0 else journal.default_debit_account_id.id,
                        'credit': 0.0 if commission.amount > 0.0 else -commission.amount,
                        'debit': commission.amount if commission.amount > 0.0 else 0.0,
                    }),
                ],
            })
            move.post()
            commission.write({'state': 'done', 'move_id': move.id})
        return True

    def action_mark_paid(self):
        if self.filtered(lambda c: c.state != 'done'):
            raise UserError('You cannot mark a commission "paid" if it is not already "done".')
        if not self:
            raise UserError('You must have at least one "done" commission.')
        payments = self._mark_paid()
        action = self.env.ref('hr_commission.action_hr_commission_payment').read()[0]
        action['res_ids'] = payments.ids
        return action

    def _mark_paid(self):
        employees = self.mapped('employee_id')
        payments = self.env['hr.commission.payment']
        for employee in employees:
            commissions = self.filtered(lambda c: c.employee_id == employee)
            min_date = False
            max_date = False
            for commission in commissions:
                if not min_date or (commission.move_date and min_date > commission.move_date):
                    min_date = commission.move_date
                if not max_date or (commission.move_date and max_date < commission.move_date):
                    max_date = commission.move_date
            payment = payments.create({
                'employee_id': employee.id,
                'name': ('Commissions %s - %s' % (min_date, max_date)),
                'date': fields.Date.today(),
            })
            payments += payment
            commissions.write({'state': 'paid', 'payment_id': payment.id})
        return payments

    def action_cancel(self):
        for commission in self:
            if commission.move_id:
                commission.move_id.write({'state': 'draft'})
                commission.move_id.unlink()
            commission.write({'state': 'cancel'})
        return True

    def action_draft(self):
        for commission in self.filtered(lambda c: c.state == 'cancel'):
            commission.write({'state': 'draft'})


class CommissionPayment(models.Model):
    _name = 'hr.commission.payment'
    _description = 'Commission Payment'
    _order = 'id desc'

    name = fields.Char(string='Name')
    employee_id = fields.Many2one('hr.employee', required=1)
    user_id = fields.Many2one('res.users', related='employee_id.user_id')
    date = fields.Date(string='Date')
    commission_ids = fields.One2many('hr.commission', 'payment_id', string='Paid Commissions', readonly=True)
    commission_count = fields.Integer(string='Commission Count', compute='_compute_commission_stats', store=True)
    commission_amount = fields.Float(string='Commission Amount', compute='_compute_commission_stats', store=True)

    @api.depends('commission_ids')
    def _compute_commission_stats(self):
        for payment in self:
            payment.commission_count = len(payment.commission_ids)
            payment.commission_amount = sum(payment.commission_ids.mapped('amount'))


class CommissionStructure(models.Model):
    _name = 'hr.commission.structure'
    _description = 'Commission Structure'
    _order = 'id desc'

    name = fields.Char(string='Name')
    line_ids = fields.One2many('hr.commission.structure.line', 'structure_id', string='Lines')

    def create_for_source_move(self, move, amount):
        self.ensure_one()
        commission_obj = self.env['hr.commission'].sudo()

        for line in self.line_ids:
            employee = line.employee_id
            rate = line.get_rate()
            if all((employee, rate)):
                contract = False
                if not line.rate:
                    # The rate must have come from the contract.
                    contract = employee.contract_id
                move.commission_ids += commission_obj.create({
                    'employee_id': employee.id,
                    'structure_id': self.id,
                    'source_move_id': move.id,
                    'base_amount': amount,
                    'rate_type': 'structure',
                    'contract_id': contract.id if contract else False,
                    'company_id': move.company_id.id,
                })


class CommissionStructureLine(models.Model):
    _name = 'hr.commission.structure.line'
    _description = 'Commission Structure Line'

    structure_id = fields.Many2one('hr.commission.structure', string='Structure', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    rate = fields.Float(string='Commission %', default=0.0, help='Leave 0.0 to use the employee\'s current contract rate.')

    def get_rate(self):
        if not self.rate:
            return self.employee_id.contract_id.commission_rate
        return self.rate
