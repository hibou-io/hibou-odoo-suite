# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields, models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def get_year(self):
        """
        # Helper method to get the year (normalized between Odoo Versions)
        :return: int year of payslip
        """
        return self.date_to.year
