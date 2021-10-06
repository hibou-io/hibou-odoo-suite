# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields, models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    # We need to be able to support more complexity,
    # namely, that different employees will be paid by different wage types as 'salary' vs 'hourly'
    wage_type = fields.Selection(related='contract_id.wage_type')

    def get_year(self):
        """
        # Helper method to get the year (normalized between Odoo Versions)
        :return: int year of payslip
        """
        return self.date_to.year

    def _get_contract_wage(self, work_type=None):
        # Override if you pay differently for different work types
        # In 14.0, this utilizes new computed field mechanism,
        # but will still get the 'wage' field by default.

        # This would be a good place to override though with a 'work type'
        # based mechanism, like a minimum rate or 'rate card' implementation
        return self.contract_id._get_contract_wage(work_type=work_type)
