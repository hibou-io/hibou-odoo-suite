from odoo import api, fields, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    fedex_account_number = fields.Char(string='FedEx Account Number')
    fedex_meter_number = fields.Char(string='FedEx Meter Number')
