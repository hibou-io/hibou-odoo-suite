import time
from odoo import fields, models


class ExceptionRule(models.Model):
    _inherit = 'exception.rule'

    website_description = fields.Text('Description for Website')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _check_sale_order_exceptions(self):
        so_exceptions = self.env['exception.rule'].search([('active', '=', True),
                                                           ('model', '=', 'sale.order'),
                                                           ('exception_type', '=', 'by_py_code')])

        reasons = []

        for ex in so_exceptions:
            # Globals won't expose modules used in exception rules python code.
            # They will have to be manually passed through params. ex [time]
            # Locals() can be used instead of defined params, but can also cause buggy behavior on return
            params = {'sale': self, 'exception': ex, 'time': time}
            try:
                exec(ex.code, globals(), params)
                if 'failed' in params:
                    desc = ex.website_description or ex.description
                    message = {'title': ex.name, 'description': desc}
                    reasons.append(message)
            except:
                pass

        return reasons
