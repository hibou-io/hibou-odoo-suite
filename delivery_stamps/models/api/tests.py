# -*- coding: utf-8 -*-
"""
    stamps.tests
    ~~~~~~~~~~~~

    Stamps.com API tests.

    :copyright: 2014 by Jonathan Zempel.
    :license: BSD, see LICENSE for more details.
"""

from .config import StampsConfiguration
from .services import StampsService
from datetime import date, datetime
from time import sleep
from unittest import TestCase
import logging
import os


logging.basicConfig()
logging.getLogger("suds.client").setLevel(logging.DEBUG)
file_path = os.path.abspath(__file__)
directory_path = os.path.dirname(file_path)
file_name = os.path.join(directory_path, "tests.cfg")
CONFIGURATION = StampsConfiguration(wsdl="testing", file_name=file_name)


def get_rate(service):
    """Get a test rate.

    :param service: Instance of the stamps service.
    """
    ret_val = service.create_shipping()
    ret_val.ShipDate = date.today().isoformat()
    ret_val.FromZIPCode = "94107"
    ret_val.ToZIPCode = "20500"
    ret_val.PackageType = "Package"
    rate = service.get_rates(ret_val)[0]
    ret_val.Amount = rate.Amount
    ret_val.ServiceType = rate.ServiceType
    ret_val.DeliverDays = rate.DeliverDays
    ret_val.DimWeighting = rate.DimWeighting
    ret_val.Zone = rate.Zone
    ret_val.RateCategory = rate.RateCategory
    ret_val.ToState = rate.ToState
    add_on = service.create_add_on()
    add_on.AddOnType = "US-A-DC"
    ret_val.AddOns.AddOnV7.append(add_on)

    return ret_val


def get_from_address(service):
    """Get a test 'from' address.

    :param service: Instance of the stamps service.
    """
    address = service.create_address()
    address.FullName = "Pickwick & Weller"
    address.Address1 = "300 Brannan St."
    address.Address2 = "Suite 405"
    address.City = "San Francisco"
    address.State = "CA"

    return service.get_address(address).Address


def get_to_address(service):
    """Get a test 'to' address.

    :param service: Instance of the stamps service.
    """
    address = service.create_address()
    address.FullName = "POTUS"
    address.Address1 = "1600 Pennsylvania Avenue NW"
    address.City = "Washington"
    address.State = "DC"

    return service.get_address(address).Address


class StampsTestCase(TestCase):

    initialized = False

    def setUp(self):
        if not StampsTestCase.initialized:
            self.service = StampsService(CONFIGURATION)
            StampsTestCase.initalized = True

    def _test_0(self):
        """Test account registration.
        """
        registration = self.service.create_registration()
        type = self.service.create("CodewordType")
        registration.Codeword1Type = type.Last4SocialSecurityNumber
        registration.Codeword1 = 1234
        registration.Codeword2Type = type.Last4DriversLicense
        registration.Codeword2 = 1234
        registration.PhysicalAddress = get_from_address(self.service)
        registration.MachineInfo.IPAddress = "127.0.0.1"
        registration.Email = "sws-support@stamps.com"
        type = self.service.create("AccountType")
        registration.AccountType = type.OfficeBasedBusiness
        result = self.service.register_account(registration)
        print result

    def _test_1(self):
        """Test postage purchase.
        """
        transaction_id = datetime.now().isoformat()
        result = self.service.add_postage(10, transaction_id=transaction_id)
        transaction_id = result.TransactionID
        status = self.service.create_purchase_status()
        seconds = 4

        while result.PurchaseStatus in (status.Pending, status.Processing):
            seconds = 32 if seconds * 2 >= 32 else seconds * 2
            print "Waiting {0:d} seconds to get status...".format(seconds)
            sleep(seconds)
            result = self.service.get_postage_status(transaction_id)

        print result

    def test_2(self):
        """Test label generation.
        """
        self.service = StampsService(CONFIGURATION)
        rate = get_rate(self.service)
        from_address = get_from_address(self.service)
        to_address = get_to_address(self.service)
        transaction_id = datetime.now().isoformat()
        label = self.service.get_label(from_address, to_address, rate,
                transaction_id=transaction_id)
        self.service.get_tracking(label.StampsTxID)
        self.service.get_tracking(label.TrackingNumber)
        self.service.remove_label(label.StampsTxID)
        print label

    def test_3(self):
        """Test authentication retry.
        """
        self.service.get_account()
        authenticator = self.service.plugin.authenticator
        self.service.get_account()
        self.service.plugin.authenticator = authenticator
        result = self.service.get_account()
        print result
