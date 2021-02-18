from odoo import fields, models
from odoo.addons.auth_admin.models.res_users import admin_auth_generate_login


class PortalWizardUser(models.TransientModel):
    _inherit = 'portal.wizard.user'

    website_id = fields.Many2one('website', string='Website')

    def admin_auth_generate_login(self):
        ir_model_access = self.env['ir.model.access']
        for row in self.filtered(lambda r: r.in_portal):
            user = row.partner_id.user_ids[0] if row.partner_id.user_ids else None
            if ir_model_access.check('res.partner', mode='unlink') and user:
                if row.website_id:
                    base_url = row.website_id.get_base_url()
                else:
                    base_url = None
                row.force_login_url = admin_auth_generate_login(self.env, user, base_url=base_url)
        self.filtered(lambda r: not r.in_portal).update({'force_login_url': ''})
