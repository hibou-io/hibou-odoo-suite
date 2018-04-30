# -*- coding: utf-8 -*-
from odoo import models, fields


class HrContract(models.Model):
    _inherit = 'hr.contract'

    paid_hourly = fields.Boolean(string="Paid Hourly", default=False)
