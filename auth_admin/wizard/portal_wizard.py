from odoo import api, fields, models, _
from ..models.res_users import admin_auth_generate_login


class PortalWizard(models.TransientModel):
    _inherit = 'portal.wizard'

    def admin_auth_generate_login(self):
        self.ensure_one()
        self.user_ids.admin_auth_generate_login()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "views": [[False, "form"]],
            "res_id": self.id,
            "target": "new",
        }


class PortalWizardUser(models.TransientModel):
    _inherit = 'portal.wizard.user'

    force_login_url = fields.Char(string='Force Login URL')

    def admin_auth_generate_login(self):
        ir_model_access = self.env['ir.model.access']
        for row in self.filtered(lambda r: r.is_portal):
            user = row.partner_id.user_ids[0] if row.partner_id.user_ids else None
            if ir_model_access.check('res.partner', mode='unlink') and user:
                row.force_login_url = admin_auth_generate_login(self.env, user)
        self.filtered(lambda r: not r.is_portal).update({'force_login_url': ''})
        return {
            'name': _('Portal Access Management'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'portal.wizard',
            'res_id': self.wizard_id.id,
            'target': 'new',
        }
