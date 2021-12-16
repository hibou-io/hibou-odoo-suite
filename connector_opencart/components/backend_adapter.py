# © 2019-2021 Hibou Corp.

from odoo.addons.component.core import AbstractComponent
from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.connector.exception import NetworkRetryableError
from .api.opencart import Opencart
from logging import getLogger
from lxml import etree

_logger = getLogger(__name__)


class BaseOpencartConnectorComponent(AbstractComponent):
    """ Base Opencart Connector Component

    All components of this connector should inherit from it.
    """
    _name = 'base.opencart.connector'
    _inherit = 'base.connector'
    _collection = 'opencart.backend'


class OpencartAdapter(AbstractComponent):

    _name = 'opencart.adapter'
    _inherit = ['base.backend.adapter', 'base.opencart.connector']

    _opencart_model = None

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
            opencart_api = getattr(self.work, 'opencart_api')
        except AttributeError:
            raise AttributeError(
                'You must provide a opencart_api attribute with a '
                'Opencart instance to be able to use the '
                'Backend Adapter.'
            )
        return opencart_api
