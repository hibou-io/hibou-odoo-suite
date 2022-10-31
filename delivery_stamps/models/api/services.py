# -*- coding: utf-8 -*-
"""
    stamps.services
    ~~~~~~~~~~~~~~~

    Stamps.com services.

    :copyright: 2014 by Jonathan Zempel.
    :license: BSD, see LICENSE for more details.
"""

from decimal import Decimal
from logging import getLogger
from re import compile
from suds import WebFault
from suds.bindings.document import Document
from suds.client import Client
from suds.plugin import MessagePlugin
from suds.sax.element import Element
from suds.sudsobject import asdict
from suds.xsd.sxbase import XBuiltin
from suds.xsd.sxbuiltin import Factory


PATTERN_HEX = r"[0-9a-fA-F]"
PATTERN_ID = r"{hex}{{8}}-{hex}{{4}}-{hex}{{4}}-{hex}{{4}}-{hex}{{12}}".format(
    hex=PATTERN_HEX)
RE_TRANSACTION_ID = compile(PATTERN_ID)


# class LogPlugin(MessagePlugin):
#     def __init__(self):
#         self.logger = getLogger('stamps2')
#         self.last_sent_raw = None
#         self.last_received_raw = None
#
#     def sending(self, context):
#         self.last_sent_raw = str(context.envelope)
#         self.logger.warning(self.last_sent_raw)
#
#     def received(self, context):
#         self.last_received_raw = str(context.reply)
#         self.logger.warning(self.last_received_raw)


class AuthenticatorPlugin(MessagePlugin):
    """Handle message authentication.

    :param credentials: Stamps API credentials.
    :param wsdl: Configured service client.
    """

    def __init__(self, credentials, client):
        self.credentials = credentials
        self.client = client
        self.authenticator = None

    def marshalled(self, context):
        """Add an authenticator token to the document before it is sent.

        :param context: The current message context.
        """
        body = context.envelope.getChild("Body")
        operation = body[0]

        if operation.name in ("AuthenticateUser", "RegisterAccount"):
            pass
        elif self.authenticator:
            namespace = operation.namespace()
            element = Element("Authenticator", ns=namespace)
            element.setText(self.authenticator)
            operation.insert(element)
        else:
            document = Document(self.client.wsdl)
            method = self.client.service.AuthenticateUser.method
            parameter = document.param_defs(method)[0]
            element = document.mkparam(method, parameter, self.credentials)
            operation.insert(element)

    def unmarshalled(self, context):
        """Store the authenticator token for the next call.

        :param context: The current message context.
        """
        if hasattr(context.reply, "Authenticator"):
            self.authenticator = context.reply.Authenticator
            del context.reply.Authenticator
        else:
            self.authenticator = None

        return context


class BaseService(object):
    """Base service.

    :param configuration: API configuration.
    """

    def __init__(self, configuration):
        Factory.maptag("decimal", XDecimal)
        self.client = Client(configuration.wsdl)
        credentials = self.create("Credentials")
        credentials.IntegrationID = configuration.integration_id
        credentials.Username = configuration.username
        credentials.Password = configuration.password
        self.plugin = AuthenticatorPlugin(credentials, self.client)
        # put in plugins=[] as well
        # self.logplugin = LogPlugin()
        self.client.set_options(plugins=[self.plugin], port=configuration.port)
        self.logger = getLogger("stamps")

    def call(self, method, **kwargs):
        """Call the given web service method.

        :param method: The name of the web service operation to call.
        :param kwargs: Method keyword-argument parameters.
        """
        self.logger.debug("%s(%s)", method, kwargs)
        instance = getattr(self.client.service, method)

        try:
            ret_val = instance(**kwargs)
        except WebFault as error:
            self.logger.warning("Retry %s", method, exc_info=True)
            self.plugin.authenticator = None

            try:  # retry with a re-authenticated user.
                ret_val = instance(**kwargs)
            except WebFault as error:
                self.logger.exception("%s retry failed", method)
                self.plugin.authenticator = None
                raise error

        return ret_val

    def create(self, wsdl_type):
        """Create an object of the given WSDL type.

        :param wsdl_type: The WSDL type to create an object for.
        """
        return self.client.factory.create(wsdl_type)


class StampsService(BaseService):
    """Stamps.com service.
    """

    def add_postage(self, amount, transaction_id=None):
        """Add postage to the account.

        :param amount: The amount of postage to purchase.
        :param transaction_id: Default `None`. ID that may be used to retry the
            purchase of this postage.
        """
        account = self.get_account()
        control = account.AccountInfo.PostageBalance.ControlTotal

        return self.call("PurchasePostage", PurchaseAmount=amount,
                ControlTotal=control, IntegratorTxID=transaction_id)

    def create_add_on(self):
        """Create a new add-on object.
        """
        return self.create("AddOnV17")

    def create_customs(self):
        """Create a new customs object.
        """
        return self.create("CustomsV7")

    def create_array_of_customs_lines(self):
        """Create a new array of customs objects.
        """
        return self.create("ArrayOfCustomsLine")

    def create_customs_lines(self):
        """Create new customs lines.
        """
        return self.create("CustomsLine")

    def create_address(self):
        """Create a new address object.
        """
        return self.create("Address")

    def create_purchase_status(self):
        """Create a new purchase status object.
        """
        return self.create("PurchaseStatus")

    def create_registration(self):
        """Create a new registration object.
        """
        ret_val = self.create("RegisterAccount")
        ret_val.IntegrationID = self.plugin.credentials.IntegrationID
        ret_val.UserName = self.plugin.credentials.Username
        ret_val.Password = self.plugin.credentials.Password

        return ret_val

    def create_extended_postage_info(self):
        return self.create("ExtendedPostageInfoV1")

    def create_shipping(self):
        """Create a new shipping object.
        """
        return self.create("RateV40")

    def get_address(self, address):
        """Get a shipping address.

        :param address: Address instance to get a clean shipping address for.
        """
        return self.call("CleanseAddress", Address=address)

    def get_account(self):
        """Get account information.
        """
        return self.call("GetAccountInfo")

    def get_label(self, rate, transaction_id, image_type=None,
            customs=None, sample=False, extended_postage_info=False):
        """Get a shipping label.

        :param from_address: The shipping 'from' address.
        :param to_address: The shipping 'to' address.
        :param rate: A rate instance for the shipment.
        :param transaction_id: ID that may be used to retry/rollback the
            purchase of this label.
        :param customs: A customs instance for international shipments.
        :param sample: Default ``False``. Get a sample label without postage.
        """
        return self.call("CreateIndicium", IntegratorTxID=transaction_id,
                Rate=rate, ImageType=image_type, Customs=customs,
                SampleOnly=sample, ExtendedPostageInfo=extended_postage_info)

    def get_postage_status(self, transaction_id):
        """Get postage purchase status.

        :param transaction_id: The transaction ID returned by
            :meth:`add_postage`.
        """
        return self.call("GetPurchaseStatus", TransactionID=transaction_id)

    def get_rates(self, shipping):
        """Get shipping rates.

        :param shipping: Shipping instance to get rates for.
        """
        rates = self.call("GetRates", Rate=shipping)

        if rates.Rates:
            ret_val = [rate for rate in rates.Rates.Rate]
        else:
            ret_val = []

        return ret_val

    def get_tracking(self, transaction_id):
        """Get tracking events for a shipment.

        :param transaction_id: The transaction ID (or tracking number) returned
            by :meth:`get_label`.
        """
        if RE_TRANSACTION_ID.match(transaction_id):
            arguments = dict(StampsTxID=transaction_id)
        else:
            arguments = dict(TrackingNumber=transaction_id)

        return self.call("TrackShipment", **arguments)

    def register_account(self, registration):
        """Register a new account.

        :param registration: Registration instance.
        """
        arguments = asdict(registration)

        return self.call("RegisterAccount", **arguments)

    def remove_label(self, transaction_id):
        """Cancel a shipping label.

        :param transaction_id: The transaction ID (or tracking number) returned
            by :meth:`get_label`.
        """
        if RE_TRANSACTION_ID.match(transaction_id):
            arguments = dict(StampsTxID=transaction_id)
        else:
            arguments = dict(TrackingNumber=transaction_id)

        return self.call("CancelIndicium", **arguments)


class XDecimal(XBuiltin):
    """Represents an XSD decimal type.
    """

    def translate(self, value, topython=True):
        """Translate between string and decimal values.

        :param value: The value to translate.
        :param topython: Default `True`. Determine whether to translate the
            value for python.
        """
        if topython:
            if isinstance(value, str) and len(value):
                ret_val = Decimal(value)
            else:
                ret_val = None
        else:
            if isinstance(value, (int, float, Decimal)):
                ret_val = str(value)
            else:
                ret_val = value

        return ret_val
