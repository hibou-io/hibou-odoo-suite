from odoo import fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    is_overtime_exempt = fields.Boolean(string='Overtime Exempt',
                                        help='e.g. Agriculture or farm work exempt under the US FLSA.')
