# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import datetime
from odoo import api, fields, models


class PublisherWarrantyContract(models.AbstractModel):
    _inherit = 'publisher_warranty.contract'

    def _get_hibou_modules(self):
        modules = super(PublisherWarrantyContract, self)._get_hibou_modules()
        try:
            today_date = fields.Date.today()
            last_thirty_date = today_date - datetime.timedelta(days=30)
            today = fields.Date.to_string(today_date + datetime.timedelta(days=1))  # Dates vs Datetimes, pad out a day
            last_thirty = fields.Date.to_string(last_thirty_date)
            self.env.cr.execute(
                'SELECT COUNT(DISTINCT(employee_id)) FROM hr_payslip WHERE create_date BETWEEN %s AND %s',
                (last_thirty, today))
            employee_count = self.env.cr.fetchone()[0] or 0
            modules.update({
                'l10n_us_hr_payroll': employee_count,
            })
        except:
            pass
        return modules
    
    @api.model
    def hibou_payroll_modules_to_update(self):
        res = super().hibou_payroll_modules_to_update()
        res.append('l10n_us_hr_payroll')
        return res
