# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import models


class PublisherWarrantyContract(models.AbstractModel):
    _inherit = 'publisher_warranty.contract'

    def _get_hibou_modules(self):
        modules = super(PublisherWarrantyContract, self)._get_hibou_modules()
        try:
            self.env.cr.execute(
                'SELECT COUNT(*) FROM pos_config WHERE pax_endpoint != \'\' AND pax_endpoint IS NOT NULL')
            pax_count = self.env.cr.fetchone()[0] or 0
            modules.update({
                'pos_pax': pax_count,
            })
        except:
            pass
        return modules
