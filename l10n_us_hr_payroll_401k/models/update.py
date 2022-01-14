# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, models


class PublisherWarrantyContract(models.AbstractModel):
    _inherit = 'publisher_warranty.contract'
    
    @api.model
    def hibou_payroll_modules_to_update(self):
        res = super().hibou_payroll_modules_to_update()
        res.append('l10n_us_hr_payroll_401k')
        return res
