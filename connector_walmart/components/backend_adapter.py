# © 2017,2018 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent
from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.connector.exception import NetworkRetryableError
from .api.walmart import Walmart
from logging import getLogger
from lxml import etree

_logger = getLogger(__name__)


class BaseWalmartConnectorComponent(AbstractComponent):
    """ Base Walmart Connector Component

    All components of this connector should inherit from it.
    """
    _name = 'base.walmart.connector'
    _inherit = 'base.connector'
    _collection = 'walmart.backend'


class WalmartAdapter(AbstractComponent):

    _name = 'walmart.adapter'
    _inherit = ['base.backend.adapter', 'base.walmart.connector']

    _walmart_model = None

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

    @property
    def api_instance(self):
        try:
            walmart_api = getattr(self.work, 'walmart_api')
        except AttributeError:
            raise AttributeError(
                'You must provide a walmart_api attribute with a '
                'Walmart instance to be able to use the '
                'Backend Adapter.'
            )
        return walmart_api
