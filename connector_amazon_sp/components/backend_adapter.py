# © 2021 Hibou Corp.

from odoo.addons.component.core import AbstractComponent

# Feed API
from datetime import datetime
from xml.etree import ElementTree


class BaseAmazonConnectorComponent(AbstractComponent):
    """ Base Amazon Connector Component

    All components of this connector should inherit from it.
    """
    _name = 'base.amazon.connector'
    _inherit = 'base.connector'
    _collection = 'amazon.backend'


class AmazonAdapter(AbstractComponent):
    _name = 'amazon.adapter'
    _inherit = ['base.backend.adapter', 'base.amazon.connector']

    ElementTree = ElementTree
    FEED_ENCODING = 'iso-8859-1'

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids """
        raise NotImplementedError

    def read(self, id, attributes=None):
        """ Returns the information of a record """
        raise NotImplementedError

    def search_read(self, filters=None):
        """ Search records according to some criterias
        and returns their information"""
        raise NotImplementedError

    def create(self, data):
        """ Create a record on the external system """
        raise NotImplementedError

    def write(self, id, data):
        """ Update records on the external system """
        raise NotImplementedError

    def delete(self, id):
        """ Delete a record on the external system """
        raise NotImplementedError

    def _feed(self, message_type, backend):
        root = self.ElementTree.Element('AmazonEnvelope',
                                        {'{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation': 'amzn-envelope.xsd'})
        header = self.ElementTree.SubElement(root, 'Header')
        self.ElementTree.SubElement(header, 'DocumentVersion').text = '1.01'
        self.ElementTree.SubElement(header, 'MerchantIdentifier').text = backend.merchant_id
        self.ElementTree.SubElement(root, 'MessageType').text = message_type

        # note that you can remove and add your own Message node
        message = self.ElementTree.SubElement(root, 'Message')
        self.ElementTree.SubElement(message, 'MessageID').text = str(int(datetime.now().timestamp()))
        return root, message

    def _feed_string(self, node):
        return self.ElementTree.tostring(node, encoding=self.FEED_ENCODING, method='xml')

    @property
    def api_instance(self):
        try:
            amazon_api = getattr(self.work, 'amazon_api')
        except AttributeError:
            raise AttributeError(
                'You must provide a amazon_api attribute with a '
                'Amazon instance to be able to use the '
                'Backend Adapter.'
            )
        return amazon_api
