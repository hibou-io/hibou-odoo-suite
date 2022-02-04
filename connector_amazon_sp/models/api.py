# © 2021 Hibou Corp.

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from base64 import b64decode, b64encode

from odoo import api
from odoo.tools import pycompat

PREFIX = 'amz_pii:'
PREFIX_LEN = len(PREFIX)
BLOCK_SIZE = 32

AMZ_PII_DECRYPT_STARTED = 1
AMZ_PII_DECRYPT_FAIL = -1


def make_amz_pii_decrypt(cipher):
    def amz_pii_decrypt(value):
        if value and isinstance(value, pycompat.string_types) and value.startswith(PREFIX):
            try:
                to_decrypt = b64decode(value[PREFIX_LEN:])
                # remove whitespace and `ack`
                return cipher.decrypt(to_decrypt).decode().strip().strip('\x06')
            except ValueError:
                pass
            except:
                raise
        return value
    return amz_pii_decrypt


def make_amz_pii_encrypt(cipher):
    def amz_pii_encrypt(value):
        if value and isinstance(value, pycompat.string_types) and not value.startswith(PREFIX):
            try:
                to_encrypt = value.encode()
                to_encrypt = pad(to_encrypt, BLOCK_SIZE)
                # must be aligned, so pad with spaces (to remove in decrypter)
                # need_padded = len(to_encrypt) % BLOCK_SIZE
                # if need_padded:
                #     to_encrypt = to_encrypt + (b' ' * (BLOCK_SIZE - need_padded))
                to_encode = cipher.encrypt(to_encrypt)
                return PREFIX + b64encode(to_encode).decode()
            except ValueError:
                pass
            except:
                raise
        return value
    return amz_pii_encrypt


def make_amz_pii_cipher(env):
    # TODO we should try to get this from environment variable
    # we should check 1. env variable 2. odoo config 3. database.secret
    get_param = env['ir.config_parameter'].sudo().get_param
    # we could get the 'database.uuid'
    database_secret = get_param('database.secret')
    if len(database_secret) < BLOCK_SIZE:
        database_secret = database_secret.ljust(BLOCK_SIZE).encode()
    else:
        database_secret = database_secret[:BLOCK_SIZE].encode()
    try:
        cipher = AES.new(database_secret, AES.MODE_ECB)
    except ValueError:
        cipher = None
    return cipher

# No PII field has been observed in this method
# def set(self, record, field, value):
#     """ Set the value of ``field`` for ``record``. """
#     amz_pii_decrypt = getattr(self, 'amz_pii_decrypt', None)
#     c = record.env.context.get('amz_pii_decrypt') or True
#     _logger.warn('set amz_pii_decrypt ' + str(c))
#     if not amz_pii_decrypt and c:
#         # setup function to do the decryption
#         get_param = record.env['ir.config_parameter'].sudo().get_param
#         prefix = 'amz_pii:'
#         prefix_len = len(prefix)
#         block_size = 32
#         # we could get the 'database.uuid'
#         database_secret = get_param('database.secret')
#         if len(database_secret) < block_size:
#             database_secret = database_secret.ljust(block_size).encode()
#         else:
#             database_secret = database_secret[:block_size].encode()
#         try:
#             cipher = AES.new(database_secret, AES.MODE_ECB)
#         except ValueError:
#             _logger.error('Cannot create AES256 decryption environment.')
#             cipher = None
#             self.amz_pii_decrypt = AMZ_PII_DECRYPT_FAIL
#
#         if cipher:
#             _logger.warn('created cipher')
#             def amz_pii_decrypt(value):
#                 _logger.warn('  amz_pii_decrypt(' + str(value) + ')')
#                 if value and isinstance(value, pycompat.string_types) and value.startswith(prefix):
#                     try:
#                         to_decrypt = b64decode(value[prefix_len:])
#                         v = cipher.decrypt(to_decrypt).decode().strip()
#                         _logger.warn('  decrypted to ' + str(v))
#                         return v
#                     except:
#                         raise
#                 return value
#             self.amz_pii_decrypt = amz_pii_decrypt
#     elif amz_pii_decrypt and not isinstance(amz_pii_decrypt, int):
#         value = amz_pii_decrypt(value)
#     key = record.env.cache_key(field)
#     self._data[key][field][record._ids[0]] = value


def update(self, records, field, values):
    amz_pii_decrypt = getattr(self, 'amz_pii_decrypt', None)
    amz_pii_decrypt_enabled = records.env.context.get('amz_pii_decrypt')
    if not amz_pii_decrypt and amz_pii_decrypt_enabled:
        self._start_amz_pii_decrypt(records.env)
    elif amz_pii_decrypt_enabled and amz_pii_decrypt and not isinstance(amz_pii_decrypt, int):
        for i, value in enumerate(values):
            values[i] = amz_pii_decrypt(value)

    key = records.env.cache_key(field)
    self._data[key][field].update(pycompat.izip(records._ids, values))


def _start_amz_pii_decrypt(self, env):
    self.amz_pii_decrypt = AMZ_PII_DECRYPT_STARTED
    cipher = make_amz_pii_cipher(env)
    if cipher:
        self.amz_pii_decrypt = make_amz_pii_decrypt(cipher)
    else:
        self.amz_pii_decrypt = AMZ_PII_DECRYPT_FAIL


# api.Cache.set = set
api.Cache.update = update
api.Cache._start_amz_pii_decrypt = _start_amz_pii_decrypt
