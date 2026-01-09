import json
import logging

from odoo import fields, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.config import config

_logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError as err:  # pragma: no cover
    _logger.debug(err)
    Fernet = None

FIELD_ENCRYPTION_KEY = "field_encryption_key"

def monkey_patch(cls):
    """ Return a method decorator to monkey-patch the given class. """
    def decorate(func):
        name = func.__name__
        func.super = getattr(cls, name, None)
        setattr(cls, name, func)
        return func
    return decorate


#
# Implement encrypt fields by monkey-patching fields.Field
#

fields.Field.__doc__ += """

        .. _field-encrypt:

        .. rubric:: Encrypt fields

        :param encrypt: the name of the field where the value of this field must be stored.
"""
fields.Field.encrypt = None

@monkey_patch(fields.Field)
def _get_attrs(self, model_class, name):
    attrs = _get_attrs.super(self, model_class, name)
    if attrs.get('encrypt'):
        # by default, encrypt fields are not stored and not copied
        attrs['store'] = False
        attrs['copy'] = attrs.get('copy', False)
        attrs['compute'] = self._compute_encrypt
        if not attrs.get('readonly'):
            attrs['inverse'] = self._inverse_encrypt
    return attrs

@monkey_patch(fields.Field)
def _compute_encrypt(self, records):
    for record in records:
        values = record[self.encrypt]
        record[self.name] = values.get(self.name)
    if self.relational:
        for record in records:
            record[self.name] = record[self.name].exists()

@monkey_patch(fields.Field)
def _inverse_encrypt(self, records):
    for record in records:
        values = record[self.encrypt]
        value = self.convert_to_read(record[self.name], record)
        if value:
            if values.get(self.name) != value:
                values[self.name] = value
                record[self.encrypt] = values
        else:
            if self.name in values:
                values.pop(self.name)
                record[self.encrypt] = values


#
# Definition and implementation of encryption fields
#

class Encryption(fields.Field):
    """ Encryption fields provide the storage for encrypt fields. """
    type = 'encryption'
    column_type = ('bytea', 'bytea')

    prefetch = False                    # not prefetched by default

    def _get_cipher(self):
        """Return a cipher using the key of environment.
        force_env = name of the env key.
        Useful for encoding against one precise env
        """
        if Fernet is None:
            raise UserError(_("The library 'cryptography' is missing, Fernet import cannot proceed."))

        key_str = config.get(FIELD_ENCRYPTION_KEY)
        if not key_str:
            raise ValidationError(
                _(
                    "No '%(key_name)s' entry found in config file. "
                    "Use a key similar to: %(key)s",
                    key_name=FIELD_ENCRYPTION_KEY,
                    key=Fernet.generate_key().decode(),
                )
            )
        # key should be in bytes format
        key = key_str.encode()
        return Fernet(key)

    def _encrypt_data(self, data):
        if not isinstance(data, bytes):
            data = data.encode()
        return self._get_cipher().encrypt(data or b'{}')

    def _decrypt_data(self, value):
        cipher = self._get_cipher()
        try:
            return cipher.decrypt(value).decode()
        except InvalidToken as exc:
            _logger.error(
                f"{self.name} has been encrypted with a different "
                "key. Unless you can recover the previous key, "
                f"this {self.name} is unreadable."
            )
            return {}

    def convert_to_column_insert(self, value, record, values=None, validate=True):
        return self.convert_to_cache(value, record, validate=validate)

    def convert_to_cache(self, value, record, validate=True):
        value = value or {}
        # cache format: json.dumps(value) or None
        return self._encrypt_data(json.dumps(value)) if isinstance(value, dict) else (value or None)

    def convert_to_record(self, value, record):
        if isinstance(value, memoryview):
            value = bytes(value)
        if isinstance(value, str):
            # the cache must contain bytes or memoryview, but sometimes a string
            # is given when assigning a binary field (test `TestFileSeparator`)
            value = value.encode()
        return json.loads(self._decrypt_data(value)) if value else {}

fields.Encryption = Encryption
