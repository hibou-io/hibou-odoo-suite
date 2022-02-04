# © 2021 Hibou Corp.

from odoo.addons.component.tests.common import SavepointComponentCase
import odoo


class AmazonTestCase(SavepointComponentCase):
    """ Base class - Test the imports from a Amazon Mock. """

    def setUp(self):
        super(AmazonTestCase, self).setUp()
        # disable commits when run from pytest/nosetest
        odoo.tools.config['test_enable'] = True
        # We need a backend configured in the db to avoid storing credentials
        self.backend = self.env['amazon.backend'].create({
            'name': 'Test',
            'api_refresh_token': 'Not null',
            'api_lwa_client_id': 'Not null',
            'api_lwa_client_secret': 'Not null',
            'api_aws_access_key': 'Not Null',
            'api_aws_secret_key': 'Not Null',
            'api_role_arn': 'Not Null',
            'merchant_id': 'Test Merchant ID',
            'payment_mode_id': self.browse_ref('account_payment_mode.payment_mode_inbound_ct1').id,
            'product_categ_id': self.browse_ref('product.product_category_1').id,
            'sale_prefix': 'TEST',
        })

    def _import_record(self, model_name, amazon_id):
        assert model_name.startswith('amazon.')

        self.env[model_name].import_record(self.backend, amazon_id)

        binding = self.env[model_name].search(
            [('backend_id', '=', self.backend.id),
             ('external_id', '=', str(amazon_id))]
        )
        self.assertEqual(len(binding), 1)
        return binding
