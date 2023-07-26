from odoo import api, fields, models, _


class InvoiceChangeWizard(models.TransientModel):
    _inherit = 'account.invoice.change'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    update_tags = fields.Selection(selection=[
        ('no', 'Do not update tags'),
        ('add', 'Add to tags'),
        ('set', 'Set tags'),
    ], default='no', string='Update Analytic Tags')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')

    def _analytic_account_id(self, invoice):
        analytics = invoice.invoice_line_ids.mapped('analytic_account_id')
        if len(analytics):
            return analytics[0].id
        return False

    @api.model
    def default_get(self, fields):
        rec = super(InvoiceChangeWizard, self).default_get(fields)
        invoice = self.env['account.move'].browse(rec['move_id'])
        rec.update({
            'analytic_account_id': self._analytic_account_id(invoice),
            'analytic_tag_ids': [(6, 0, invoice.invoice_line_ids.analytic_tag_ids.ids)],
        })
        return rec

    def affect_change(self):
        res = super(InvoiceChangeWizard, self).affect_change()
        self._affect_analytic_change()
        return res
    
    def _prepare_analytic_values(self):
        vals = {
            'analytic_account_id': self.analytic_account_id.id,
            'analytic_line_ids': [(5, 0, 0)],
        }
        tag_commands = []
        if self.update_tags == 'add':
            tag_commands = [(4, tag.id, 0) for tag in self.analytic_tag_ids]
        if self.update_tags == 'set':
            tag_commands = [(6, 0, self.analytic_tag_ids.ids)]
        if tag_commands:
            vals['analytic_tag_ids'] = tag_commands
        return vals

    def _affect_analytic_change(self):
        lines_to_affect = self.move_id.invoice_line_ids
        lines_to_affect.write(self._prepare_analytic_values())
        lines_to_affect.create_analytic_lines()
