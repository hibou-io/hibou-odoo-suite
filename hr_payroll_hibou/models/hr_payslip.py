# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    # From IRS Publication 15-T or logically (annually, bi-monthly)
    PAY_PERIODS_IN_YEAR = {
            'annually':        1,
            'semi-annually':   2,
            'quarterly':       4,
            'bi-monthly':      6,
            'monthly':        12,
            'semi-monthly':   24,
            'bi-weekly':      26,
            'weekly':         52,
            'daily':         260,
        }

    # normal_wage is an integer field, but that lacks precision.
    normal_wage = fields.Float(compute='_compute_normal_wage', store=True)
    # We need to be able to support more complexity,
    # namely, that different employees will be paid by different wage types as 'salary' vs 'hourly'
    wage_type = fields.Selection(related='contract_id.wage_type')

    @api.depends('contract_id')
    def _compute_normal_wage(self):
        with_contract = self.filtered('contract_id')
        # fixes bug in original computation if the size of the recordset is >1
        (self - with_contract).update({'normal_wage': 0.0})
        for payslip in with_contract:
            payslip.normal_wage = payslip._get_contract_wage()

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

    def get_pay_periods_in_year(self):
        return self.PAY_PERIODS_IN_YEAR.get(self.contract_id.schedule_pay, 0)
