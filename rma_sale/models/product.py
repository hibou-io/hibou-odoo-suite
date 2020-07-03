# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    rma_sale_validity = fields.Integer(string='RMA Eligible Days (Sale)',
                                       help='Determines the number of days from the time '
                                            'of the sale that the product is eligible to '
                                            'be returned. 0 (default) will allow the product '
                                            'to be returned for an indefinite period of time. '
                                            'A positive number will allow the product to be '
                                            'returned up to that number of days. A negative '
                                            'number prevents the return of the product.')
