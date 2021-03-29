from odoo import fields, models


class ExceptionRule(models.Model):
    _inherit = 'exception.rule'

    website_description = fields.Text('Description for Website')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _check_sale_order_exceptions(self):
        exception_ids = self.detect_exceptions()
        exceptions = self.env['exception.rule'].browse(exception_ids)
        reasons = [{'title': ex.name, 'description': ex.website_description or ex.description} for ex in exceptions]
        return reasons
