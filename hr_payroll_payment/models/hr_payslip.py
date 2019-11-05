# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    @api.depends('slip_ids.is_paid')
    def _is_paid(self):
        for run in self:
            run.is_paid = all(run.slip_ids.mapped('is_paid'))

    is_paid = fields.Boolean(string="Payslips Paid", compute='_is_paid', store=True)
    date = fields.Date('Date Account', states={'draft': [('readonly', False)], 'verify': [('readonly', False)]},
                       readonly=True,
                       help="Keep empty to use the period of the validation(Payslip) date.")
    batch_payment_id = fields.Many2one('account.batch.payment', string='Payment Batch')

    def action_register_payment(self):
        action = self.mapped('slip_ids').action_register_payment()
        payments = self.env['account.payment'].browse(action['res_ids'])
        batch_action = payments.create_batch_payment()
        self.write({'batch_payment_id': batch_action['res_id']})
        return batch_action

    def write(self, values):
        if 'date' in values:
            slips = self.mapped('slip_ids').filtered(lambda s: s.state in ('draft', 'verify'))
            slips.write({'date': values['date']})
        return super().write(values)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.depends('move_id', 'move_id.line_ids.full_reconcile_id')
    def _is_paid(self):
        for payslip in self:
            payslip.is_paid = (
                payslip.move_id and len(payslip.move_id.line_ids.filtered(lambda l: (
                    l.partner_id == payslip.employee_id.address_home_id and
                    l.account_id.internal_type == 'payable' and
                    not l.reconciled
                ))) == 0
            )

    is_paid = fields.Boolean(string="Has been Paid", compute='_is_paid', store=True)

    @api.model
    def create(self, vals):
        if 'date' in self.env.context:
            vals['date'] = self.env.context.get('date')
        return super(HrPayslip, self).create(vals)

    def _payment_values(self, amount):
        values = {
            'payment_reference': self.number,
            'communication': self.number + ' - ' + self.name,
            'journal_id': self.move_id.journal_id.payroll_payment_journal_id.id,
            'payment_method_id': self.move_id.journal_id.payroll_payment_method_id.id,
            'partner_type': 'supplier',
            'partner_id': self.employee_id.address_home_id.id,
            'payment_type': 'outbound',
            'amount': -amount,
        }
        if amount > 0.0:
            values.update({
                'payment_type': 'inbound',
                'amount': amount,
                'payment_method_id': self.move_id.journal_id.payroll_payment_method_refund_id.id,
            })
        return values

    def action_register_payment(self):
        if not all(slip.move_id.journal_id.payroll_payment_journal_id for slip in self):
            raise UserError(_('Payroll Payment journal not configured on the existing entry\'s journal.'))
        if not all(slip.move_id.journal_id.payroll_payment_method_id for slip in self):
            raise UserError(_('Payroll Payment method not configured on the existing entry\'s journal.'))

        payments = self.env['account.payment']
        for slip in self.filtered(lambda s: s.move_id and not s.is_paid):
            lines_to_pay = slip.move_id.line_ids.filtered(lambda l: l.partner_id == slip.employee_id.address_home_id
                         and l.account_id == slip.employee_id.address_home_id.property_account_payable_id)
            amount = sum(lines_to_pay.mapped('amount_residual'))
            payment_values = slip._payment_values(amount)
            payment = payments.create(payment_values)
            payment.post()
            lines_paid = payment.move_line_ids.filtered(lambda l: l.account_id == slip.employee_id.address_home_id.property_account_payable_id)
            lines_to_reconcile = lines_to_pay + lines_paid
            lines_to_reconcile.reconcile()
            payments += payment
        action = self.env.ref('account.action_account_payments_payable').read()[0]
        action.update({
            'res_ids': payments.ids,
            'domain': [('id', 'in', payments.ids)],
        })
        return action

    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        self._generate_move()
        return res

    def _generate_move(self):
        """
             Generate the accounting entries related to the selected payslips
             A move is created for each journal and for each month.
         """
        # Not needed after abstraction

        #res = super(HrPayslip, self).action_payslip_done()
        #precision = self.env['decimal.precision'].precision_get('Payroll')

        # Add payslip without run
        payslips_to_post = self.filtered(lambda slip: not slip.payslip_run_id)

        # Adding pay slips from a batch and deleting pay slips with a batch that is not ready for validation.
        payslip_runs = (self - payslips_to_post).mapped('payslip_run_id')
        for run in payslip_runs:
            if run._are_payslips_ready():
                payslips_to_post |= run.slip_ids

        # A payslip need to have a done state and not an accounting move.
        payslips_to_post = payslips_to_post.filtered(lambda slip: slip.state == 'done' and not slip.move_id)

        # Check that a journal exists on all the structures
        if any(not payslip.struct_id for payslip in payslips_to_post):
            raise ValidationError(_('One of the contract for these payslips has no structure type.'))
        if any(not structure.journal_id for structure in payslips_to_post.mapped('struct_id')):
            raise ValidationError(_('One of the payroll structures has no account journal defined on it.'))

        # Map all payslips by structure journal and pay slips month.
        # {'journal_id': {'month': [slip_ids]}}
        # slip_mapped_data = {
        #     slip.struct_id.journal_id.id: {fields.Date().end_of(slip.date_to, 'month'): self.env['hr.payslip']} for slip
        #     in
        #     payslips_to_post}
        # Hibou Customization: group with journal itself so that journal behavior can be derived.
        slip_mapped_data = {
            slip.struct_id.journal_id: {fields.Date().end_of(slip.date_to, 'month'): self.env['hr.payslip']} for slip
            in
            payslips_to_post}
        for slip in payslips_to_post:
            slip_mapped_data[slip.struct_id.journal_id][fields.Date().end_of(slip.date_to, 'month')] |= slip

        for journal in slip_mapped_data:  # For each journal_id.
            """
            All methods to generate journal entry should generate one or more 
            journal entries given this format.
            """
            for slip_date in slip_mapped_data[journal]:  # For each month.
                if hasattr(self, '_generate_move_' + str(journal.payroll_entry_type)):
                    getattr(self, '_generate_move_' + str(journal.payroll_entry_type))(slip_mapped_data, journal, slip_date)
                else:
                    self._generate_move_original(slip_mapped_data, journal, slip_date)

    def _check_slips_employee_home_address(self):
        employees_missing_partner = self.mapped('employee_id').filtered(lambda e: not e.address_home_id)
        if employees_missing_partner:
            raise UserError(_('The following employees are missing private addresses. %s') % \
                            (', '.join(employees_missing_partner.mapped('name'))))
        address_ap = self.mapped('employee_id.address_home_id.property_account_payable_id')
        if len(address_ap) > 1:
            raise UserError(_('Employee\'s private address account payable not the same for all addresses.'))

    def _process_journal_lines_grouped(self, line_ids, date, precision):
        slip = self
        employee_partner_id = slip.employee_id.address_home_id.id
        for line in slip.line_ids.filtered(lambda l: l.category_id):
            amount = -line.total if slip.credit_note else line.total
            if line.code == 'NET':  # Check if the line is the 'Net Salary'.
                for tmp_line in slip.line_ids.filtered(lambda l: l.category_id):
                    if tmp_line.salary_rule_id.not_computed_in_net:  # Check if the rule must be computed in the 'Net Salary' or not.
                        if amount > 0:
                            amount -= abs(tmp_line.total)
                        elif amount < 0:
                            amount += abs(tmp_line.total)
            if float_is_zero(amount, precision_digits=precision):
                continue
            debit_account_id = line.salary_rule_id.account_debit.id
            credit_account_id = line.salary_rule_id.account_credit.id
            partner_id = line.salary_rule_id.partner_id.id or employee_partner_id

            if debit_account_id:  # If the rule has a debit account.
                debit = amount if amount > 0.0 else 0.0
                credit = -amount if amount < 0.0 else 0.0

                existing_debit_lines = (
                    line_id for line_id in line_ids if
                    # line_id['name'] == line.name
                    line_id['partner_id'] == partner_id
                    and line_id['account_id'] == debit_account_id
                    and ((line_id['debit'] > 0 and credit <= 0) or (line_id['credit'] > 0 and debit <= 0)))
                debit_line = next(existing_debit_lines, False)

                if not debit_line:
                    debit_line = {
                        'name': line.name,
                        'partner_id': partner_id,
                        'account_id': debit_account_id,
                        'journal_id': slip.struct_id.journal_id.id,
                        'date': date,
                        'debit': debit,
                        'credit': credit,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id.id or slip.contract_id.analytic_account_id.id,
                    }
                    line_ids.append(debit_line)
                else:
                    line_name_pieces = set(debit_line['name'].split(', '))
                    line_name_pieces.add(line.name)
                    debit_line['name'] = ', '.join(line_name_pieces)
                    debit_line['debit'] += debit
                    debit_line['credit'] += credit

            if credit_account_id:  # If the rule has a credit account.
                debit = -amount if amount < 0.0 else 0.0
                credit = amount if amount > 0.0 else 0.0
                existing_credit_line = (
                    line_id for line_id in line_ids if
                    # line_id['name'] == line.name
                    line_id['partner_id'] == partner_id
                    and line_id['account_id'] == credit_account_id
                    and ((line_id['debit'] > 0 and credit <= 0) or (line_id['credit'] > 0 and debit <= 0))
                )
                credit_line = next(existing_credit_line, False)

                if not credit_line:
                    credit_line = {
                        'name': line.name,
                        'partner_id': partner_id,
                        'account_id': credit_account_id,
                        'journal_id': slip.struct_id.journal_id.id,
                        'date': date,
                        'debit': debit,
                        'credit': credit,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id.id or slip.contract_id.analytic_account_id.id,
                    }
                    line_ids.append(credit_line)
                else:
                    line_name_pieces = set(credit_line['name'].split(', '))
                    line_name_pieces.add(line.name)
                    credit_line['name'] = ', '.join(line_name_pieces)
                    credit_line['debit'] += debit
                    credit_line['credit'] += credit

    def _generate_move_grouped(self, slip_mapped_data, journal, slip_date):
        slip_mapped_data[journal][slip_date]._check_slips_employee_home_address()

        precision = self.env['decimal.precision'].precision_get('Payroll')
        line_ids = []
        debit_sum = 0.0
        credit_sum = 0.0
        date = slip_date
        move_dict = {
            'narration': '',
            'ref': date.strftime('%B %Y'),
            'journal_id': journal.id,
            'date': date,
        }

        for slip in slip_mapped_data[journal][slip_date]:
            move_dict['narration'] += slip.number or '' + ' - ' + slip.employee_id.name or ''
            move_dict['narration'] += '\n'
            slip._process_journal_lines_grouped(line_ids, date, precision)

        for line_id in line_ids:  # Get the debit and credit sum.
            debit_sum += line_id['debit']
            credit_sum += line_id['credit']

        # The code below is called if there is an error in the balance between credit and debit sum.
        if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
            acc_id = slip.journal_id.default_credit_account_id.id
            if not acc_id:
                raise UserError(
                    _('The Expense Journal "%s" has not properly configured the Credit Account!') % (
                        slip.journal_id.name))
            existing_adjustment_line = (
                line_id for line_id in line_ids if line_id['name'] == _('Adjustment Entry')
            )
            adjust_credit = next(existing_adjustment_line, False)

            if not adjust_credit:
                adjust_credit = {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': 0.0,
                    'credit': debit_sum - credit_sum,
                }
                line_ids.append(adjust_credit)
            else:
                adjust_credit['credit'] = debit_sum - credit_sum

        elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
            acc_id = slip.journal_id.default_debit_account_id.id
            if not acc_id:
                raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (
                    slip.journal_id.name))
            existing_adjustment_line = (
                line_id for line_id in line_ids if line_id['name'] == _('Adjustment Entry')
            )
            adjust_debit = next(existing_adjustment_line, False)

            if not adjust_debit:
                adjust_debit = {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': credit_sum - debit_sum,
                    'credit': 0.0,
                }
                line_ids.append(adjust_debit)
            else:
                adjust_debit['debit'] = credit_sum - debit_sum

        # Add accounting lines in the move
        move_dict['line_ids'] = [(0, 0, line_vals) for line_vals in line_ids]
        move = self.env['account.move'].create(move_dict)
        for slip in slip_mapped_data[journal][slip_date]:
            slip.write({'move_id': move.id, 'date': date})

    def _generate_move_slip(self, slip_mapped_data, journal, slip_date):
        slip_mapped_data[journal][slip_date]._check_slips_employee_home_address()

        precision = self.env['decimal.precision'].precision_get('Payroll')

        for slip in slip_mapped_data[journal][slip_date]:
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            date = slip_date
            move_dict = {
                'narration': '',
                'ref': date.strftime('%B %Y'),
                'journal_id': journal.id,
                'date': date,
            }

            move_dict['narration'] += slip.number or '' + ' - ' + slip.employee_id.name or ''
            move_dict['narration'] += '\n'
            slip._process_journal_lines_grouped(line_ids, date, precision)

            for line_id in line_ids:  # Get the debit and credit sum.
                debit_sum += line_id['debit']
                credit_sum += line_id['credit']

            # The code below is called if there is an error in the balance between credit and debit sum.
            if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_credit_account_id.id
                if not acc_id:
                    raise UserError(
                        _('The Expense Journal "%s" has not properly configured the Credit Account!') % (
                            slip.journal_id.name))
                existing_adjustment_line = (
                    line_id for line_id in line_ids if line_id['name'] == _('Adjustment Entry')
                )
                adjust_credit = next(existing_adjustment_line, False)

                if not adjust_credit:
                    adjust_credit = {
                        'name': _('Adjustment Entry'),
                        'partner_id': False,
                        'account_id': acc_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': 0.0,
                        'credit': debit_sum - credit_sum,
                    }
                    line_ids.append(adjust_credit)
                else:
                    adjust_credit['credit'] = debit_sum - credit_sum

            elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_debit_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (
                        slip.journal_id.name))
                existing_adjustment_line = (
                    line_id for line_id in line_ids if line_id['name'] == _('Adjustment Entry')
                )
                adjust_debit = next(existing_adjustment_line, False)

                if not adjust_debit:
                    adjust_debit = {
                        'name': _('Adjustment Entry'),
                        'partner_id': False,
                        'account_id': acc_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': credit_sum - debit_sum,
                        'credit': 0.0,
                    }
                    line_ids.append(adjust_debit)
                else:
                    adjust_debit['debit'] = credit_sum - debit_sum

            # Add accounting lines in the move
            move_dict['line_ids'] = [(0, 0, line_vals) for line_vals in line_ids]
            move = self.env['account.move'].create(move_dict)
            slip.write({'move_id': move.id, 'date': date})

    def _generate_move_original(self, slip_mapped_data, journal, slip_date):
        """
        Odoo's original version.
        Fixed bug with 'matching' credit line
        """
        precision = self.env['decimal.precision'].precision_get('Payroll')
        line_ids = []
        debit_sum = 0.0
        credit_sum = 0.0
        date = slip_date
        move_dict = {
            'narration': '',
            'ref': date.strftime('%B %Y'),
            'journal_id': journal.id,
            'date': date,
        }

        for slip in slip_mapped_data[journal][slip_date]:
            move_dict['narration'] += slip.number or '' + ' - ' + slip.employee_id.name or ''
            move_dict['narration'] += '\n'
            for line in slip.line_ids.filtered(lambda l: l.category_id):
                amount = -line.total if slip.credit_note else line.total
                if line.code == 'NET':  # Check if the line is the 'Net Salary'.
                    for tmp_line in slip.line_ids.filtered(lambda l: l.category_id):
                        if tmp_line.salary_rule_id.not_computed_in_net:  # Check if the rule must be computed in the 'Net Salary' or not.
                            if amount > 0:
                                amount -= abs(tmp_line.total)
                            elif amount < 0:
                                amount += abs(tmp_line.total)
                if float_is_zero(amount, precision_digits=precision):
                    continue

                debit_account_id = line.salary_rule_id.account_debit.id
                credit_account_id = line.salary_rule_id.account_credit.id

                if debit_account_id:  # If the rule has a debit account.
                    debit = amount if amount > 0.0 else 0.0
                    credit = -amount if amount < 0.0 else 0.0

                    existing_debit_lines = (
                        line_id for line_id in line_ids if
                        line_id['name'] == line.name
                        and line_id['account_id'] == debit_account_id
                        and ((line_id['debit'] > 0 and credit <= 0) or (line_id['credit'] > 0 and debit <= 0)))
                    debit_line = next(existing_debit_lines, False)

                    if not debit_line:
                        debit_line = {
                            'name': line.name,
                            'partner_id': False,
                            'account_id': debit_account_id,
                            'journal_id': slip.struct_id.journal_id.id,
                            'date': date,
                            'debit': debit,
                            'credit': credit,
                            'analytic_account_id': line.salary_rule_id.analytic_account_id.id or slip.contract_id.analytic_account_id.id,
                        }
                        line_ids.append(debit_line)
                    else:
                        debit_line['debit'] += debit
                        debit_line['credit'] += credit

                if credit_account_id:  # If the rule has a credit account.
                    debit = -amount if amount < 0.0 else 0.0
                    credit = amount if amount > 0.0 else 0.0
                    existing_credit_line = (
                        line_id for line_id in line_ids if
                        line_id['name'] == line.name
                        and line_id['account_id'] == credit_account_id
                        and ((line_id['debit'] > 0 and credit <= 0) or (line_id['credit'] > 0 and debit <= 0))
                    )
                    credit_line = next(existing_credit_line, False)

                    if not credit_line:
                        credit_line = {
                            'name': line.name,
                            'partner_id': False,
                            'account_id': credit_account_id,
                            'journal_id': slip.struct_id.journal_id.id,
                            'date': date,
                            'debit': debit,
                            'credit': credit,
                            'analytic_account_id': line.salary_rule_id.analytic_account_id.id or slip.contract_id.analytic_account_id.id,
                        }
                        line_ids.append(credit_line)
                    else:
                        credit_line['debit'] += debit
                        credit_line['credit'] += credit

        for line_id in line_ids:  # Get the debit and credit sum.
            debit_sum += line_id['debit']
            credit_sum += line_id['credit']

        # The code below is called if there is an error in the balance between credit and debit sum.
        if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
            acc_id = slip.journal_id.default_credit_account_id.id
            if not acc_id:
                raise UserError(
                    _('The Expense Journal "%s" has not properly configured the Credit Account!') % (
                        slip.journal_id.name))
            existing_adjustment_line = (
                line_id for line_id in line_ids if line_id['name'] == _('Adjustment Entry')
            )
            adjust_credit = next(existing_adjustment_line, False)

            if not adjust_credit:
                adjust_credit = {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': 0.0,
                    'credit': debit_sum - credit_sum,
                }
                line_ids.append(adjust_credit)
            else:
                adjust_credit['credit'] = debit_sum - credit_sum

        elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
            acc_id = slip.journal_id.default_debit_account_id.id
            if not acc_id:
                raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (
                    slip.journal_id.name))
            existing_adjustment_line = (
                line_id for line_id in line_ids if line_id['name'] == _('Adjustment Entry')
            )
            adjust_debit = next(existing_adjustment_line, False)

            if not adjust_debit:
                adjust_debit = {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': credit_sum - debit_sum,
                    'credit': 0.0,
                }
                line_ids.append(adjust_debit)
            else:
                adjust_debit['debit'] = credit_sum - debit_sum

        # Add accounting lines in the move
        move_dict['line_ids'] = [(0, 0, line_vals) for line_vals in line_ids]
        move = self.env['account.move'].create(move_dict)
        for slip in slip_mapped_data[journal][slip_date]:
            slip.write({'move_id': move.id, 'date': date})
