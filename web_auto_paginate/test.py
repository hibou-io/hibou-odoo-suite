# include this file and depend on 'stock' to test on cancel button
# This intentionally introduces a lot of delay around stock pickings
# to help test the UI's responsiveness.

from time import sleep
from odoo import api, models

import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_cancel(self):
        super().action_cancel()
        return {
            'auto_paginate': True,
        }

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        _logger.warn('sleeping')
        sleep(1)
        return super().read(fields=fields, load=load)
