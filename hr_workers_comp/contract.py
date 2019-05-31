from odoo import api,fields,models


class HRContract(models.Model):
    _inherit = 'hr.contract'

    wc_code_id = fields.Many2one('hr.wc_code', string='Workers Comp. Code')


class WorkersCompensationClass(models.Model):
    _name = 'hr.wc_code'
    _description = "Workers Comp. Code"
    _rec_name = 'display_name'
    _order = 'code'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name')
    code = fields.Char('Code')
    rate = fields.Float('Rate', digits=(7, 6), company_dependent=True)
    display_name = fields.Char(compute='_compute_clean_display_name', store=True)

    @api.depends('name', 'code')
    def _compute_clean_display_name(self):
        for rec in self:
            rec.display_name = '%s %s' % (rec.code, rec.name)
