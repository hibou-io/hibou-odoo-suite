from odoo import api, fields, models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def create(self, vals):
        if 'date' in self.env.context:
            vals['date'] = self.env.context.get('date')
        return super(HrPayslip, self).create(vals)


class PayslipBatch(models.Model):
    _inherit = 'hr.payslip.run'

    date = fields.Date('Date Account', states={'draft': [('readonly', False)]}, readonly=True,
        help="Keep empty to use the period of the validation(Payslip) date.")

    def write(self, values):
        if 'date' in values or 'journal_id' in values:
            slips = self.mapped('slip_ids').filtered(lambda s: s.state in ('draft', 'verify'))
            slip_values = {}
            if 'date' in values:
                slip_values['date'] = values['date']
            if 'journal_id' in values:
                slip_values['journal_id'] = values['journal_id']
            slips.write(slip_values)

        return super(PayslipBatch, self).write(values)
