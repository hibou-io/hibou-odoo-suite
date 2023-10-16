from odoo import api, _
from odoo.exceptions import UserError
from odoo.addons.product.models.product_attribute import ProductAttribute


def write(self, vals):
    """Override to make sure attribute type can't be changed if it's used on
    a product template.

    This is important to prevent because changing the type would make
    existing combinations invalid without recomputing them, and recomputing
    them might take too long and we don't want to change products without
    the user knowing about it."""
    if 'create_variant' in vals:
        for pa in self:
            
            if vals['create_variant'] != pa.create_variant:
                if not pa.number_related_products:
                    # index this attribute, this will be free if there are truely no related products
                    pa._compute_products()
                if pa.number_related_products:
                    raise UserError(
                        _("You cannot change the Variants Creation Mode of the attribute %s because it is used on the following products:\n%s") %
                        (pa.display_name, ", ".join(pa.product_tmpl_ids.mapped('display_name')))
                    )
    invalidate = 'sequence' in vals and any(record.sequence != vals['sequence'] for record in self)
    res = super(ProductAttribute, self).write(vals)
    if invalidate:
        # prefetched o2m have to be resequenced
        # (eg. product.template: attribute_line_ids)
        self.env.flush_all()
        self.env.invalidate_all()
    return res

ProductAttribute.write = write

# eventually may want to only display if count is <100 otherwise this takes a long long time
@api.ondelete(at_uninstall=False)
def _unlink_except_used_on_product(self):
    for pa in self:
        if not pa.number_related_products:
             # index this attribute, this will be free if there are truely no related products
            pa._compute_products()
        if pa.number_related_products:
            if pa.number_related_products > 100:
                raise UserError(
                    _("You cannot delete the attribute %s because it is used on many products.") %
                    (pa.display_name, )
                )
            else:
                raise UserError(
                    _("You cannot delete the attribute %s because it is used on the following products:\n%s") %
                    (pa.display_name, ", ".join(pa.product_tmpl_ids.mapped('display_name')))
                )

ProductAttribute._unlink_except_used_on_product = _unlink_except_used_on_product

# this method should never be called as it is not a computed field anymore
# replace it to replace decoration
# @api.depends('product_tmpl_ids')
def _compute_number_related_products(self):
    pass
    # raise Exception('in patched _compute_number_related_products')
    # for pa in self:
    #     pa.number_related_products = len(pa.product_tmpl_ids)

ProductAttribute._compute_number_related_products = _compute_number_related_products

# this method should be called on a schedule to "index" these...
# replace it to replace decoration
# @api.depends('attribute_line_ids.active', 'attribute_line_ids.product_tmpl_id')
def _compute_products(self):
    for pa in self:
        product_tmpls = pa.attribute_line_ids.product_tmpl_id
        pa.with_context(active_test=False).product_tmpl_ids = product_tmpls
        pa.number_related_products = len(product_tmpls)
        

ProductAttribute._compute_products = _compute_products
