# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models

class PurchaseUserTest(models.Model):
    _name = 'base.exception.test.purchase'
    _inherit = 'base.exception.test.purchase'

    def button_confirm(self):
        if self.detect_exceptions():
            return self._popup_exceptions()
        super(PurchaseUserTest, self).button_confirm()

    @api.model
    def _get_popup_action(self):
        return self.env['ir.actions.act_window'].sudo().create(
            {'name': 'Outstanding exceptions to manage',
             'type': 'ir.actions.act_window',
             'view_id': self.env.ref('base_exception.view_exception_rule_confirm').id,
             'res_model': 'purchase.test.exception.rule.confirm',
             'target': 'new',
             'view_mode': 'form',
             })


class PurchaseTestExceptionRuleConfirm(models.TransientModel):
    _name = 'purchase.test.exception.rule.confirm'
    _description = 'Exception Rule Confirm Wizard'
    _inherit = 'exception.rule.confirm'

    related_model_id = fields.Many2one('base.exception.test.purchase')
