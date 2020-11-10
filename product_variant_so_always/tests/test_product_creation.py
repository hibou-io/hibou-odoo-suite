from odoo.tests import common
from odoo.exceptions import UserError


class TestProductCreation(common.TransactionCase):
    def setUp(self):
        super(TestProductCreation, self).setUp()
        self.attrs = []

        # Create 1000 combinations
        for a in range(1, 4):
            attribute = self.env['product.attribute'].create({
                'name': 'Attr ' + str(a),
                'create_variant': 'always',
            })
            self.attrs.append(attribute)
            for v in range(1, 11):
                self.env['product.attribute.value'].create({
                    'name': 'Value ' + str(v),
                    'attribute_id': attribute.id,
                })
        # Create 1 more...
        self.env['product.attribute.value'].create({
            'name': 'Value 11',
            'attribute_id': self.attrs[0].id,
        })

    def test_01_product_template(self):
        product_tmpl = self.env['product.template'].create({
            'name': 'Test Product',
            'type': 'product',
        })
        attr_line_model = self.env['product.template.attribute.line']

        with self.assertRaises(UserError):
            for a in self.attrs:
                attr_line_model.create({
                    'product_tmpl_id': product_tmpl.id,
                    'attribute_id': a.id,
                    'value_ids': [(6, 0, a.value_ids.ids)],
                })

        product_tmpl.always_variant_on_so = True
        for a in self.attrs:
            attr_line_model.create({
                'product_tmpl_id': product_tmpl.id,
                'attribute_id': a.id,
                'value_ids': [(6, 0, a.value_ids.ids)],
            })
