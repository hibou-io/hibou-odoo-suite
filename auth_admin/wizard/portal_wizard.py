from odoo import api, fields, models
from ..models.res_users import admin_auth_generate_login


class PortalWizard(models.TransientModel):
    _inherit = 'portal.wizard'

    @api.multi
    def admin_auth_generate_login(self):
        self.ensure_one()
        self.user_ids.admin_auth_generate_login()
        return {'type': 'ir.actions.do_nothing'}


class PortalWizardUser(models.TransientModel):
    _inherit = 'portal.wizard.user'

    force_login_url = fields.Char(string='Force Login URL')

    @api.multi
    def admin_auth_generate_login(self):
        ir_model_access = self.env['ir.model.access']
        for row in self:
            row.force_login_url = ''
            user = row.partner_id.user_ids[0] if row.partner_id.user_ids else None
            if ir_model_access.check('res.partner', mode='unlink') and row.in_portal and user:
                row.force_login_url = admin_auth_generate_login(self.env, user)
