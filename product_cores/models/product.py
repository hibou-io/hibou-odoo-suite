# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    core_ok = fields.Boolean(string='Core')
    product_core_service_id = fields.Many2one('product.product', string='Product Core Deposit',
                                              compute='_compute_product_core_service',
                                              inverse='_set_product_core_service')
    product_core_id = fields.Many2one('product.product', string='Product Core',
                                      compute='_compute_product_core',
                                      inverse='_set_product_core')
    product_core_validity = fields.Integer(string='Product Core Return Validity',
                                           help='How long after a sale the core is eligible for return. (in days)')

    @api.depends('product_variant_ids', 'product_variant_ids.product_core_service_id')
    def _compute_product_core_service(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.product_core_service_id = template.product_variant_ids.product_core_service_id
        for template in (self - unique_variants):
            template.product_core_service_id = False

    @api.depends('product_variant_ids', 'product_variant_ids.product_core_id')
    def _compute_product_core(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.product_core_id = template.product_variant_ids.product_core_id
        for template in (self - unique_variants):
            template.product_core_id = False

    def _set_product_core_service(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.product_core_service_id = self.product_core_service_id

    def _set_product_core(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.product_core_id = self.product_core_id


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_core_service_id = fields.Many2one('product.product', string='Product Core Deposit')
    product_core_id = fields.Many2one('product.product', string='Product Core')

    def get_purchase_core_service(self, vendor):
        seller_line = self.seller_ids.filtered(lambda l: l.name == vendor and l.product_core_service_id)
        # only want to return the first one
        for l in seller_line:
            return l.product_core_service_id
        return seller_line


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    product_core_service_id = fields.Many2one('product.product', string='Product Core Deposit')
