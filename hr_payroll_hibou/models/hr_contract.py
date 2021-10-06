from odoo import fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    wage_type = fields.Selection([('monthly', 'Period Fixed Wage'), ('hourly', 'Hourly Wage')],
                                 default='monthly', required=True, related=False)

    def _get_contract_wage(self, work_type=None):
        # Override if you pay differently for different work types
        # In 14.0, this utilizes new computed field mechanism,
        # but will still get the 'wage' field by default.
        self.ensure_one()
        return self[self._get_contract_wage_field(work_type=work_type)]

    def _get_contract_wage_field(self, work_type=None):
        if self.wage_type == 'hourly':
            return 'hourly_wage'
        return super()._get_contract_wage_field()
