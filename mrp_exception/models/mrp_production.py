from odoo import api, fields, models


class ExceptionRule(models.Model):
    _inherit = 'exception.rule'

    model = fields.Selection(
        selection_add=[
            ('mrp.production', 'Production'),
        ],
        ondelete={
            'mrp.production': 'cascade',
        },
    )
    production_ids = fields.Many2many('mrp.production', string="Productions")


class MrpProduction(models.Model):
    _inherit = ['mrp.production', 'base.exception']
    _name = 'mrp.production'

    @api.model
    def _reverse_field(self):
        return 'production_ids'

    @api.model
    def _get_popup_action(self):
        return self.env.ref('mrp_exception.action_mrp_production_exception_confirm')

    def action_confirm(self):
        self.ensure_one()
        if self.detect_exceptions():
            return self._popup_exceptions()
        return super().action_confirm()
