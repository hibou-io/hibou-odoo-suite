import json
import os
from unittest.mock import MagicMock, patch, PropertyMock

from cryptography.fernet import Fernet

from odoo import fields, models
from odoo.exceptions import ValidationError, UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools.config import config

from odoo.addons.hibou_field_encryption.models.fields import (
    DEFAULT_ENCRYPTION_FIELD,
    Encryption,
    EncryptionKeyring,
    GCP_PROJECT,
    GCP_SECRET_NAME,
    REC_ENCRYPTION_KEY,
    REC_ENCRYPTION_KEY_PROVIDER,
    _KEY_PROVIDERS,
    _load_keyring_from_gcp,
    _pack_header,
    _unpack_header,
    get_keyring,
    migrate_fields_to_encryption,
    re_encrypt_blob,
    re_encrypt_table,
    reset_keyring,
)
from odoo.addons.hibou_field_encryption.models.models import ICP_ENCRYPTION_KEY_VERSION

TEST_KEY = Fernet.generate_key().decode()

ALL_CONFIG_KEYS = (
    REC_ENCRYPTION_KEY,
    REC_ENCRYPTION_KEY_PROVIDER,
    GCP_PROJECT,
    GCP_SECRET_NAME,
)


def setup_test_model(env, model_clses):
    model_names = set()
    for model_cls in model_clses:
        model = model_cls._build_model(env.registry, env.cr)
        model_names.add(model._name)
    env.registry.setup_models(env.cr)
    env.registry.init_models(
        env.cr,
        model_names,
        dict(env.context, update_custom_fields=True),
    )


def _save_and_clear(*keys):
    saved = {}
    for key in keys:
        saved[key] = (config.options.get(key), os.environ.get(key.upper()))
        config.options.pop(key, None)
        os.environ.pop(key.upper(), None)
    return saved


def _restore(saved):
    for key, (cfg_val, env_val) in saved.items():
        if cfg_val is not None:
            config[key] = cfg_val
        else:
            config.options.pop(key, None)
        if env_val is not None:
            os.environ[key.upper()] = env_val
        else:
            os.environ.pop(key.upper(), None)


class EncryptPartnerExplicit(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    my_blob = fields.Encryption()
    secret_note = fields.Char(encrypt="my_blob")
    secret_code = fields.Char(encrypt="my_blob")


class EncryptPartnerSugar(models.Model):
    _name = "enc.test.sugar"
    _description = "Sugar Encryption Test"

    name = fields.Char()
    secret_one = fields.Char(encrypt=True)
    secret_two = fields.Char(encrypt=True)


@tagged("post_install", "-at_install")
class TestEncryptFieldsExplicit(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.environ[REC_ENCRYPTION_KEY.upper()] = TEST_KEY
        reset_keyring()
        setup_test_model(cls.env, [EncryptPartnerExplicit])

    @classmethod
    def tearDownClass(cls):
        os.environ.pop(REC_ENCRYPTION_KEY.upper(), None)
        reset_keyring()
        super().tearDownClass()

    def test_write_and_read_single_field(self):
        partner = self.env["res.partner"].create({"name": "Test", "secret_note": "hello"})
        self.assertEqual(partner.secret_note, "hello")

    def test_write_and_read_multiple_fields(self):
        partner = self.env["res.partner"].create({
            "name": "Test",
            "secret_note": "note1",
            "secret_code": "code1",
        })
        self.assertEqual(partner.secret_note, "note1")
        self.assertEqual(partner.secret_code, "code1")

    def test_shared_blob(self):
        partner = self.env["res.partner"].create({
            "name": "Test",
            "secret_note": "note1",
            "secret_code": "code1",
        })
        blob = partner.my_blob
        self.assertIn("secret_note", blob)
        self.assertIn("secret_code", blob)
        self.assertEqual(blob["secret_note"], "note1")
        self.assertEqual(blob["secret_code"], "code1")

    def test_update_field(self):
        partner = self.env["res.partner"].create({"name": "Test", "secret_note": "v1"})
        partner.secret_note = "v2"
        self.assertEqual(partner.secret_note, "v2")

    def test_clear_field(self):
        partner = self.env["res.partner"].create({
            "name": "Test",
            "secret_note": "value",
            "secret_code": "keep",
        })
        partner.secret_note = False
        self.assertFalse(partner.secret_note)
        self.assertEqual(partner.secret_code, "keep")


@tagged("post_install", "-at_install")
class TestEncryptTrueSugar(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.environ[REC_ENCRYPTION_KEY.upper()] = TEST_KEY
        reset_keyring()
        setup_test_model(cls.env, [EncryptPartnerSugar])

    @classmethod
    def tearDownClass(cls):
        os.environ.pop(REC_ENCRYPTION_KEY.upper(), None)
        reset_keyring()
        super().tearDownClass()

    def test_auto_encryption_field_created(self):
        model = self.env["enc.test.sugar"]
        self.assertIn(DEFAULT_ENCRYPTION_FIELD, model._fields)
        field = model._fields[DEFAULT_ENCRYPTION_FIELD]
        self.assertIsInstance(field, Encryption)

    def test_encrypt_true_read_write(self):
        rec = self.env["enc.test.sugar"].create({
            "name": "Test",
            "secret_one": "alpha",
            "secret_two": "beta",
        })
        self.assertEqual(rec.secret_one, "alpha")
        self.assertEqual(rec.secret_two, "beta")

    def test_encrypt_true_shared_blob(self):
        rec = self.env["enc.test.sugar"].create({
            "name": "Test",
            "secret_one": "alpha",
            "secret_two": "beta",
        })
        blob = rec[DEFAULT_ENCRYPTION_FIELD]
        self.assertEqual(blob.get("secret_one"), "alpha")
        self.assertEqual(blob.get("secret_two"), "beta")

    def test_encrypt_true_update(self):
        rec = self.env["enc.test.sugar"].create({"name": "Test", "secret_one": "v1"})
        rec.secret_one = "v2"
        self.assertEqual(rec.secret_one, "v2")


@tagged("post_install", "-at_install")
class TestEncryptionKeySources(TransactionCase):

    def setUp(self):
        super().setUp()
        self._saved = _save_and_clear(*ALL_CONFIG_KEYS)

    def tearDown(self):
        _restore(self._saved)
        reset_keyring()
        super().tearDown()

    def test_key_from_env_var(self):
        os.environ[REC_ENCRYPTION_KEY.upper()] = TEST_KEY
        reset_keyring()
        enc = Encryption()
        cipher = enc._get_cipher()
        data = b"test data"
        encrypted = cipher.encrypt(data)
        self.assertEqual(cipher.decrypt(encrypted), data)

    def test_key_from_config(self):
        config[REC_ENCRYPTION_KEY] = TEST_KEY
        reset_keyring()
        enc = Encryption()
        cipher = enc._get_cipher()
        data = b"test data"
        encrypted = cipher.encrypt(data)
        self.assertEqual(cipher.decrypt(encrypted), data)

    def test_config_takes_precedence_over_env(self):
        key1 = Fernet.generate_key().decode()
        key2 = Fernet.generate_key().decode()
        config[REC_ENCRYPTION_KEY] = key1
        os.environ[REC_ENCRYPTION_KEY.upper()] = key2
        reset_keyring()
        enc = Encryption()
        cipher = enc._get_cipher()
        test_cipher = Fernet(key1.encode())
        data = b"precedence test"
        encrypted = cipher.encrypt(data)
        self.assertEqual(test_cipher.decrypt(encrypted), data)

    def test_no_key_raises_error(self):
        reset_keyring()
        enc = Encryption()
        with self.assertRaises(ValidationError):
            enc._get_cipher()

    def test_unknown_provider_raises(self):
        os.environ[REC_ENCRYPTION_KEY_PROVIDER.upper()] = "does_not_exist"
        reset_keyring()
        with self.assertRaises(ValidationError):
            get_keyring()

    def test_default_provider_is_config(self):
        os.environ[REC_ENCRYPTION_KEY.upper()] = TEST_KEY
        reset_keyring()
        kr = get_keyring()
        self.assertEqual(kr.current_version, 0)

    def test_explicit_config_provider(self):
        os.environ[REC_ENCRYPTION_KEY_PROVIDER.upper()] = "config"
        os.environ[REC_ENCRYPTION_KEY.upper()] = TEST_KEY
        reset_keyring()
        kr = get_keyring()
        self.assertEqual(kr.current_version, 0)


# --------------------------------------------------------------------------
# Keyring unit tests
# --------------------------------------------------------------------------

@tagged("post_install", "-at_install")
class TestEncryptionKeyring(TransactionCase):

    def setUp(self):
        super().setUp()
        self._saved = _save_and_clear(*ALL_CONFIG_KEYS)

    def tearDown(self):
        _restore(self._saved)
        reset_keyring()
        super().tearDown()

    def test_single_key_creates_version_zero(self):
        os.environ[REC_ENCRYPTION_KEY.upper()] = TEST_KEY
        reset_keyring()
        kr = get_keyring()
        self.assertEqual(kr.current_version, 0)
        self.assertEqual(len(kr), 1)
        self.assertIn(0, kr)

    def test_multi_key_config(self):
        k0 = Fernet.generate_key().decode()
        k1 = Fernet.generate_key().decode()
        k2 = Fernet.generate_key().decode()
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"0:{k0},1:{k1},2:{k2}"
        reset_keyring()
        kr = get_keyring()
        self.assertEqual(kr.current_version, 2)
        self.assertEqual(len(kr), 3)
        self.assertIn(0, kr)
        self.assertIn(1, kr)
        self.assertIn(2, kr)

    def test_current_fernet_encrypts_with_latest(self):
        k0 = Fernet.generate_key().decode()
        k1 = Fernet.generate_key().decode()
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"0:{k0},1:{k1}"
        reset_keyring()
        kr = get_keyring()
        ct = kr.current_fernet.encrypt(b"hello")
        self.assertEqual(Fernet(k1.encode()).decrypt(ct), b"hello")

    def test_old_key_still_decrypts(self):
        k0 = Fernet.generate_key().decode()
        k1 = Fernet.generate_key().decode()
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"0:{k0},1:{k1}"
        reset_keyring()
        kr = get_keyring()
        old_ct = Fernet(k0.encode()).encrypt(b"legacy")
        self.assertEqual(kr.fernet_for_version(0).decrypt(old_ct), b"legacy")

    def test_missing_version_raises(self):
        os.environ[REC_ENCRYPTION_KEY.upper()] = TEST_KEY
        reset_keyring()
        kr = get_keyring()
        with self.assertRaises(ValidationError):
            kr.fernet_for_version(99)

    def test_empty_keyring_raises(self):
        kr = EncryptionKeyring({})
        with self.assertRaises(ValidationError):
            _ = kr.current_version


# --------------------------------------------------------------------------
# Wire-format header tests
# --------------------------------------------------------------------------

@tagged("post_install", "-at_install")
class TestWireFormat(TransactionCase):

    def test_header_roundtrip(self):
        header = _pack_header(42)
        self.assertEqual(len(header), 3)
        ver, rest = _unpack_header(header + b"ciphertext")
        self.assertEqual(ver, 42)
        self.assertEqual(rest, b"ciphertext")

    def test_legacy_blob_returns_version_zero(self):
        legacy = Fernet(TEST_KEY.encode()).encrypt(b'{"x":"y"}')
        ver, ct = _unpack_header(legacy)
        self.assertEqual(ver, 0)
        self.assertEqual(ct, legacy)

    def test_header_version_zero(self):
        header = _pack_header(0)
        ver, _ = _unpack_header(header + b"data")
        self.assertEqual(ver, 0)

    def test_header_max_version(self):
        header = _pack_header(65535)
        ver, _ = _unpack_header(header + b"data")
        self.assertEqual(ver, 65535)


# --------------------------------------------------------------------------
# Versioned encrypt/decrypt through the Encryption field
# --------------------------------------------------------------------------

@tagged("post_install", "-at_install")
class TestVersionedEncryption(TransactionCase):

    def setUp(self):
        super().setUp()
        self._saved = _save_and_clear(*ALL_CONFIG_KEYS)

    def tearDown(self):
        _restore(self._saved)
        reset_keyring()
        super().tearDown()

    def test_encrypt_tags_current_version(self):
        os.environ[REC_ENCRYPTION_KEY.upper()] = TEST_KEY
        reset_keyring()
        enc = Encryption()
        blob = enc._encrypt_data(json.dumps({"a": "b"}))
        ver, _ = _unpack_header(blob)
        self.assertEqual(ver, 0)

    def test_encrypt_tags_latest_version(self):
        k0 = Fernet.generate_key().decode()
        k5 = Fernet.generate_key().decode()
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"0:{k0},5:{k5}"
        reset_keyring()
        enc = Encryption()
        blob = enc._encrypt_data(json.dumps({"a": "b"}))
        ver, _ = _unpack_header(blob)
        self.assertEqual(ver, 5)

    def test_decrypt_old_version(self):
        k0 = Fernet.generate_key().decode()
        k1 = Fernet.generate_key().decode()
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"0:{k0},1:{k1}"
        reset_keyring()
        enc = Encryption()
        old_ct = Fernet(k0.encode()).encrypt(json.dumps({"x": "old"}).encode())
        old_blob = _pack_header(0) + old_ct
        result = json.loads(enc._decrypt_data(old_blob))
        self.assertEqual(result, {"x": "old"})

    def test_decrypt_current_version(self):
        k0 = Fernet.generate_key().decode()
        k1 = Fernet.generate_key().decode()
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"0:{k0},1:{k1}"
        reset_keyring()
        enc = Encryption()
        blob = enc._encrypt_data(json.dumps({"y": "new"}))
        result = json.loads(enc._decrypt_data(blob))
        self.assertEqual(result, {"y": "new"})

    def test_decrypt_legacy_untagged_blob(self):
        """Blobs without a version header (written before keyring) still work."""
        os.environ[REC_ENCRYPTION_KEY.upper()] = TEST_KEY
        reset_keyring()
        enc = Encryption()
        legacy_ct = Fernet(TEST_KEY.encode()).encrypt(json.dumps({"legacy": True}).encode())
        result = json.loads(enc._decrypt_data(legacy_ct))
        self.assertEqual(result, {"legacy": True})

    def test_decrypt_revoked_key_returns_empty(self):
        k1 = Fernet.generate_key().decode()
        k2 = Fernet.generate_key().decode()
        revoked = Fernet.generate_key().decode()
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"1:{k1},2:{k2}"
        reset_keyring()
        enc = Encryption()
        enc.name = "test_field"
        ct = Fernet(revoked.encode()).encrypt(b'{"gone": true}')
        blob = _pack_header(99) + ct
        result = enc._decrypt_data(blob)
        self.assertEqual(result, '{}')


# --------------------------------------------------------------------------
# re_encrypt helpers
# --------------------------------------------------------------------------

@tagged("post_install", "-at_install")
class TestReEncrypt(TransactionCase):

    def setUp(self):
        super().setUp()
        self._saved = _save_and_clear(*ALL_CONFIG_KEYS)

    def tearDown(self):
        _restore(self._saved)
        reset_keyring()
        super().tearDown()

    def test_re_encrypt_blob_changes_version(self):
        k0 = Fernet.generate_key().decode()
        k1 = Fernet.generate_key().decode()
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"0:{k0},1:{k1}"
        reset_keyring()
        old_ct = Fernet(k0.encode()).encrypt(b'{"data":"secret"}')
        old_blob = _pack_header(0) + old_ct
        changed, new_blob = re_encrypt_blob(old_blob)
        self.assertTrue(changed)
        ver, new_ct = _unpack_header(new_blob)
        self.assertEqual(ver, 1)
        self.assertEqual(Fernet(k1.encode()).decrypt(new_ct), b'{"data":"secret"}')

    def test_re_encrypt_blob_noop_if_current(self):
        os.environ[REC_ENCRYPTION_KEY.upper()] = TEST_KEY
        reset_keyring()
        enc = Encryption()
        blob = enc._encrypt_data('{"x": 1}')
        changed, new_blob = re_encrypt_blob(blob)
        self.assertFalse(changed)
        self.assertEqual(blob, new_blob)

    def test_re_encrypt_blob_empty(self):
        changed, result = re_encrypt_blob(None)
        self.assertFalse(changed)
        self.assertIsNone(result)


@tagged("post_install", "-at_install")
class TestReEncryptTable(TransactionCase):
    TABLE = "test_reencrypt_tbl"

    def setUp(self):
        super().setUp()
        self._saved = _save_and_clear(*ALL_CONFIG_KEYS)
        self.k0 = Fernet.generate_key().decode()
        self.k1 = Fernet.generate_key().decode()
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"0:{self.k0},1:{self.k1}"
        reset_keyring()

        cr = self.env.cr
        cr.execute(
            'CREATE TABLE IF NOT EXISTS "{}" ('
            "id SERIAL PRIMARY KEY, "
            '"{}" bytea'
            ")".format(self.TABLE, DEFAULT_ENCRYPTION_FIELD)
        )

    def tearDown(self):
        self.env.cr.execute('DROP TABLE IF EXISTS "{}"'.format(self.TABLE))
        _restore(self._saved)
        reset_keyring()
        super().tearDown()

    def _insert_blob(self, data_dict, key_version=0):
        kr = get_keyring()
        fernet = kr.fernet_for_version(key_version)
        ct = fernet.encrypt(json.dumps(data_dict).encode())
        blob = _pack_header(key_version) + ct
        cr = self.env.cr
        cr.execute(
            'INSERT INTO "{}" ("{}") VALUES (%s) RETURNING id'.format(
                self.TABLE, DEFAULT_ENCRYPTION_FIELD
            ),
            (blob,),
        )
        return cr.fetchone()[0]

    def _read_raw_blob(self, rec_id):
        cr = self.env.cr
        cr.execute(
            'SELECT "{}" FROM "{}" WHERE id = %s'.format(
                DEFAULT_ENCRYPTION_FIELD, self.TABLE
            ),
            (rec_id,),
        )
        row = cr.fetchone()
        return bytes(row[0]) if row and row[0] else None

    def test_re_encrypt_table_updates_old_rows(self):
        r1 = self._insert_blob({"a": "1"}, key_version=0)
        r2 = self._insert_blob({"b": "2"}, key_version=0)
        updated = re_encrypt_table(self.env.cr, self.TABLE)
        self.assertEqual(updated, 2)
        for rid in (r1, r2):
            raw = self._read_raw_blob(rid)
            ver, _ = _unpack_header(raw)
            self.assertEqual(ver, 1)

    def test_re_encrypt_table_skips_current_rows(self):
        self._insert_blob({"a": "1"}, key_version=1)
        updated = re_encrypt_table(self.env.cr, self.TABLE)
        self.assertEqual(updated, 0)

    def test_re_encrypt_table_mixed(self):
        self._insert_blob({"old": "data"}, key_version=0)
        self._insert_blob({"new": "data"}, key_version=1)
        updated = re_encrypt_table(self.env.cr, self.TABLE)
        self.assertEqual(updated, 1)

    def test_re_encrypt_preserves_data(self):
        original = {"secret": "preserve_me", "code": "42"}
        rid = self._insert_blob(original, key_version=0)
        re_encrypt_table(self.env.cr, self.TABLE)
        raw = self._read_raw_blob(rid)
        ver, ct = _unpack_header(raw)
        self.assertEqual(ver, 1)
        kr = get_keyring()
        plaintext = kr.fernet_for_version(1).decrypt(ct).decode()
        self.assertEqual(json.loads(plaintext), original)


# --------------------------------------------------------------------------
# GCP Secret Manager key provider
# --------------------------------------------------------------------------

class _MockSecretPayload:
    def __init__(self, data):
        self.data = data


class _MockSecretVersionResponse:
    def __init__(self, data_bytes):
        self.payload = _MockSecretPayload(data_bytes)


class _MockSecretVersion:
    def __init__(self, name):
        self.name = name


class _MockSecretManagerClient:
    """In-memory mock of ``SecretManagerServiceClient``."""

    def __init__(self, versions=None):
        self._versions = versions or {}

    def list_secret_versions(self, request):
        return [
            _MockSecretVersion(name)
            for name in sorted(self._versions)
        ]

    def access_secret_version(self, request):
        name = request["name"]
        if name not in self._versions:
            raise Exception(f"Version {name} not found")
        return _MockSecretVersionResponse(self._versions[name])


@tagged("post_install", "-at_install")
class TestGCPKeyProvider(TransactionCase):

    def setUp(self):
        super().setUp()
        self._saved = _save_and_clear(*ALL_CONFIG_KEYS)

    def tearDown(self):
        _restore(self._saved)
        reset_keyring()
        super().tearDown()

    def _setup_gcp_env(self):
        os.environ[REC_ENCRYPTION_KEY_PROVIDER.upper()] = "gcp_secret_manager"
        os.environ[GCP_PROJECT.upper()] = "test-project"
        os.environ[GCP_SECRET_NAME.upper()] = "odoo-enc-key"

    def test_gcp_provider_missing_project_raises(self):
        os.environ[REC_ENCRYPTION_KEY_PROVIDER.upper()] = "gcp_secret_manager"
        os.environ[GCP_SECRET_NAME.upper()] = "some-secret"
        reset_keyring()
        with self.assertRaises(ValidationError):
            get_keyring()

    def test_gcp_provider_missing_secret_raises(self):
        os.environ[REC_ENCRYPTION_KEY_PROVIDER.upper()] = "gcp_secret_manager"
        os.environ[GCP_PROJECT.upper()] = "some-project"
        reset_keyring()
        with self.assertRaises(ValidationError):
            get_keyring()

    def test_gcp_loads_single_version(self):
        self._setup_gcp_env()
        k1 = Fernet.generate_key()
        mock_client = _MockSecretManagerClient({
            "projects/test-project/secrets/odoo-enc-key/versions/1": k1,
        })
        with patch(
            "odoo.addons.hibou_field_encryption.models.fields.secretmanager"
        ) as mock_sm:
            mock_sm.SecretManagerServiceClient.return_value = mock_client
            reset_keyring()
            kr = get_keyring()
        self.assertEqual(len(kr), 1)
        self.assertEqual(kr.current_version, 1)
        ct = kr.current_fernet.encrypt(b"test")
        self.assertEqual(Fernet(k1).decrypt(ct), b"test")

    def test_gcp_loads_multiple_versions(self):
        self._setup_gcp_env()
        k1 = Fernet.generate_key()
        k2 = Fernet.generate_key()
        k3 = Fernet.generate_key()
        mock_client = _MockSecretManagerClient({
            "projects/test-project/secrets/odoo-enc-key/versions/1": k1,
            "projects/test-project/secrets/odoo-enc-key/versions/2": k2,
            "projects/test-project/secrets/odoo-enc-key/versions/3": k3,
        })
        with patch(
            "odoo.addons.hibou_field_encryption.models.fields.secretmanager"
        ) as mock_sm:
            mock_sm.SecretManagerServiceClient.return_value = mock_client
            reset_keyring()
            kr = get_keyring()
        self.assertEqual(len(kr), 3)
        self.assertEqual(kr.current_version, 3)
        self.assertIn(1, kr)
        self.assertIn(2, kr)
        self.assertIn(3, kr)

    def test_gcp_current_version_is_highest(self):
        self._setup_gcp_env()
        k1 = Fernet.generate_key()
        k5 = Fernet.generate_key()
        mock_client = _MockSecretManagerClient({
            "projects/test-project/secrets/odoo-enc-key/versions/1": k1,
            "projects/test-project/secrets/odoo-enc-key/versions/5": k5,
        })
        with patch(
            "odoo.addons.hibou_field_encryption.models.fields.secretmanager"
        ) as mock_sm:
            mock_sm.SecretManagerServiceClient.return_value = mock_client
            reset_keyring()
            kr = get_keyring()
        self.assertEqual(kr.current_version, 5)
        ct = kr.current_fernet.encrypt(b"hello")
        self.assertEqual(Fernet(k5).decrypt(ct), b"hello")

    def test_gcp_old_version_decrypts(self):
        self._setup_gcp_env()
        k1 = Fernet.generate_key()
        k2 = Fernet.generate_key()
        mock_client = _MockSecretManagerClient({
            "projects/test-project/secrets/odoo-enc-key/versions/1": k1,
            "projects/test-project/secrets/odoo-enc-key/versions/2": k2,
        })
        with patch(
            "odoo.addons.hibou_field_encryption.models.fields.secretmanager"
        ) as mock_sm:
            mock_sm.SecretManagerServiceClient.return_value = mock_client
            reset_keyring()
            kr = get_keyring()
        old_ct = Fernet(k1).encrypt(b"old data")
        self.assertEqual(kr.fernet_for_version(1).decrypt(old_ct), b"old data")

    def test_gcp_invalid_key_skipped(self):
        self._setup_gcp_env()
        k1 = Fernet.generate_key()
        mock_client = _MockSecretManagerClient({
            "projects/test-project/secrets/odoo-enc-key/versions/1": k1,
            "projects/test-project/secrets/odoo-enc-key/versions/2": b"not-a-valid-fernet-key",
        })
        with patch(
            "odoo.addons.hibou_field_encryption.models.fields.secretmanager"
        ) as mock_sm:
            mock_sm.SecretManagerServiceClient.return_value = mock_client
            reset_keyring()
            kr = get_keyring()
        self.assertEqual(len(kr), 1)
        self.assertEqual(kr.current_version, 1)

    def test_gcp_no_valid_keys_raises(self):
        self._setup_gcp_env()
        mock_client = _MockSecretManagerClient({
            "projects/test-project/secrets/odoo-enc-key/versions/1": b"bad-key",
        })
        with patch(
            "odoo.addons.hibou_field_encryption.models.fields.secretmanager"
        ) as mock_sm:
            mock_sm.SecretManagerServiceClient.return_value = mock_client
            reset_keyring()
            with self.assertRaises(ValidationError):
                get_keyring()

    def test_gcp_encrypt_decrypt_roundtrip(self):
        """Full roundtrip: GCP provides keys, encrypt field uses them."""
        self._setup_gcp_env()
        k1 = Fernet.generate_key()
        k2 = Fernet.generate_key()
        mock_client = _MockSecretManagerClient({
            "projects/test-project/secrets/odoo-enc-key/versions/1": k1,
            "projects/test-project/secrets/odoo-enc-key/versions/2": k2,
        })
        with patch(
            "odoo.addons.hibou_field_encryption.models.fields.secretmanager"
        ) as mock_sm:
            mock_sm.SecretManagerServiceClient.return_value = mock_client
            reset_keyring()
            enc = Encryption()
            blob = enc._encrypt_data(json.dumps({"secret": "gcp_managed"}))
            ver, _ = _unpack_header(blob)
            self.assertEqual(ver, 2)
            result = json.loads(enc._decrypt_data(blob))
            self.assertEqual(result, {"secret": "gcp_managed"})

    def test_gcp_re_encrypt_from_old_version(self):
        """Data encrypted with old GCP version re-encrypts to latest."""
        self._setup_gcp_env()
        k1 = Fernet.generate_key()
        k2 = Fernet.generate_key()
        mock_client = _MockSecretManagerClient({
            "projects/test-project/secrets/odoo-enc-key/versions/1": k1,
            "projects/test-project/secrets/odoo-enc-key/versions/2": k2,
        })
        with patch(
            "odoo.addons.hibou_field_encryption.models.fields.secretmanager"
        ) as mock_sm:
            mock_sm.SecretManagerServiceClient.return_value = mock_client
            reset_keyring()
            old_ct = Fernet(k1).encrypt(b'{"rotated":"data"}')
            old_blob = _pack_header(1) + old_ct
            changed, new_blob = re_encrypt_blob(old_blob)
            self.assertTrue(changed)
            ver, new_ct = _unpack_header(new_blob)
            self.assertEqual(ver, 2)
            self.assertEqual(Fernet(k2).decrypt(new_ct), b'{"rotated":"data"}')


# --------------------------------------------------------------------------
# Migration helper (existing tests preserved)
# --------------------------------------------------------------------------

@tagged("post_install", "-at_install")
class TestMigrateFieldsToEncryption(TransactionCase):
    TABLE = "test_enc_migration"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.environ[REC_ENCRYPTION_KEY.upper()] = TEST_KEY
        reset_keyring()

    @classmethod
    def tearDownClass(cls):
        os.environ.pop(REC_ENCRYPTION_KEY.upper(), None)
        reset_keyring()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.cr = self.env.cr
        self.cr.execute(
            'CREATE TABLE IF NOT EXISTS "{}" ('
            "id SERIAL PRIMARY KEY, "
            "name VARCHAR, "
            "secret VARCHAR, "
            "other_secret VARCHAR"
            ")".format(self.TABLE)
        )

    def tearDown(self):
        self.cr.execute('DROP TABLE IF EXISTS "{}"'.format(self.TABLE))
        super().tearDown()

    def _insert_row(self, name, secret=None, other_secret=None):
        self.cr.execute(
            'INSERT INTO "{}" (name, secret, other_secret) VALUES (%s, %s, %s) RETURNING id'.format(self.TABLE),
            (name, secret, other_secret),
        )
        return self.cr.fetchone()[0]

    def _read_blob(self, rec_id, encryption_field=DEFAULT_ENCRYPTION_FIELD):
        self.cr.execute(
            'SELECT "{}" FROM "{}" WHERE id = %s'.format(encryption_field, self.TABLE),
            (rec_id,),
        )
        row = self.cr.fetchone()
        if not row or not row[0]:
            return {}
        raw = bytes(row[0]) if isinstance(row[0], memoryview) else row[0]
        enc = Encryption()
        return json.loads(enc._decrypt_data(raw))

    def test_basic_migration(self):
        rid = self._insert_row("Alice", secret="s3cret")
        migrate_fields_to_encryption(self.cr, self.TABLE, ["secret"])
        data = self._read_blob(rid)
        self.assertEqual(data["secret"], "s3cret")

    def test_multiple_fields(self):
        rid = self._insert_row("Bob", secret="s1", other_secret="s2")
        migrate_fields_to_encryption(self.cr, self.TABLE, ["secret", "other_secret"])
        data = self._read_blob(rid)
        self.assertEqual(data["secret"], "s1")
        self.assertEqual(data["other_secret"], "s2")

    def test_null_values_skipped(self):
        rid = self._insert_row("Carol", secret="yes", other_secret=None)
        migrate_fields_to_encryption(self.cr, self.TABLE, ["secret", "other_secret"])
        data = self._read_blob(rid)
        self.assertEqual(data["secret"], "yes")
        self.assertNotIn("other_secret", data)

    def test_merge_with_existing_blob(self):
        rid = self._insert_row("Dave", secret="new_secret")
        enc = Encryption()
        existing = enc._encrypt_data(json.dumps({"already": "here"}))
        self.cr.execute(
            'ALTER TABLE "{}" ADD COLUMN IF NOT EXISTS "{}" bytea'.format(
                self.TABLE, DEFAULT_ENCRYPTION_FIELD
            )
        )
        self.cr.execute(
            'UPDATE "{}" SET "{}" = %s WHERE id = %s'.format(
                self.TABLE, DEFAULT_ENCRYPTION_FIELD
            ),
            (existing, rid),
        )
        migrate_fields_to_encryption(self.cr, self.TABLE, ["secret"])
        data = self._read_blob(rid)
        self.assertEqual(data["already"], "here")
        self.assertEqual(data["secret"], "new_secret")

    def test_encryption_column_auto_created(self):
        self._insert_row("Eve", secret="val")
        self.cr.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %s AND column_name = %s",
            (self.TABLE, DEFAULT_ENCRYPTION_FIELD),
        )
        self.assertFalse(self.cr.fetchone())
        migrate_fields_to_encryption(self.cr, self.TABLE, ["secret"])
        self.cr.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %s AND column_name = %s",
            (self.TABLE, DEFAULT_ENCRYPTION_FIELD),
        )
        self.assertTrue(self.cr.fetchone())

    def test_drop_columns(self):
        self._insert_row("Frank", secret="val", other_secret="val2")
        migrate_fields_to_encryption(
            self.cr, self.TABLE, ["secret", "other_secret"], drop_columns=True
        )
        self.cr.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %s AND column_name IN ('secret', 'other_secret')",
            (self.TABLE,),
        )
        self.assertFalse(self.cr.fetchall())

    def test_drop_columns_false_keeps_columns(self):
        self._insert_row("Grace", secret="val")
        migrate_fields_to_encryption(
            self.cr, self.TABLE, ["secret"], drop_columns=False
        )
        self.cr.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %s AND column_name = 'secret'",
            (self.TABLE,),
        )
        self.assertTrue(self.cr.fetchone())

    def test_nonexistent_columns_ignored(self):
        self._insert_row("Hank", secret="val")
        migrate_fields_to_encryption(
            self.cr, self.TABLE, ["secret", "does_not_exist"]
        )
        data = self._read_blob(self._get_first_id())
        self.assertEqual(data["secret"], "val")

    def test_no_matching_columns_noop(self):
        self._insert_row("Ivy")
        migrate_fields_to_encryption(self.cr, self.TABLE, ["does_not_exist"])
        self.cr.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %s AND column_name = %s",
            (self.TABLE, DEFAULT_ENCRYPTION_FIELD),
        )
        self.assertFalse(self.cr.fetchone())

    def test_multiple_rows(self):
        r1 = self._insert_row("Row1", secret="a")
        r2 = self._insert_row("Row2", secret="b")
        r3 = self._insert_row("Row3", secret=None)
        migrate_fields_to_encryption(self.cr, self.TABLE, ["secret"])
        self.assertEqual(self._read_blob(r1)["secret"], "a")
        self.assertEqual(self._read_blob(r2)["secret"], "b")
        self.assertEqual(self._read_blob(r3), {})

    def test_custom_encryption_field_name(self):
        self._insert_row("Custom", secret="val")
        custom_field = "my_custom_enc"
        migrate_fields_to_encryption(
            self.cr, self.TABLE, ["secret"], encryption_field=custom_field
        )
        self.cr.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %s AND column_name = %s",
            (self.TABLE, custom_field),
        )
        self.assertTrue(self.cr.fetchone())
        data = self._read_blob(self._get_first_id(), encryption_field=custom_field)
        self.assertEqual(data["secret"], "val")

    def _get_first_id(self):
        self.cr.execute('SELECT id FROM "{}" ORDER BY id LIMIT 1'.format(self.TABLE))
        return self.cr.fetchone()[0]


    # --------------------------------------------------------------------------
    # Cron re-encryption tests
    # --------------------------------------------------------------------------

@tagged("post_install", "-at_install")
class TestCronReEncrypt(TransactionCase):
    TABLE = "test_cron_reencrypt"

    def setUp(self):
        super().setUp()
        self._saved = _save_and_clear(*ALL_CONFIG_KEYS)
        self.k0 = Fernet.generate_key().decode()
        self.k1 = Fernet.generate_key().decode()
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"0:{self.k0},1:{self.k1}"
        reset_keyring()
        self.icp = self.env['ir.config_parameter'].sudo()
        self.icp.set_param(ICP_ENCRYPTION_KEY_VERSION, '0')

    def tearDown(self):
        self.env.cr.execute('DROP TABLE IF EXISTS "{}"'.format(self.TABLE))
        self.icp.set_param(ICP_ENCRYPTION_KEY_VERSION, False)
        _restore(self._saved)
        reset_keyring()
        super().tearDown()

    def _create_test_table_with_blob(self, data_dict, key_version=0):
        cr = self.env.cr
        cr.execute(
            'CREATE TABLE IF NOT EXISTS "{}" ('
            "id SERIAL PRIMARY KEY, "
            '"{}" bytea'
            ")".format(self.TABLE, DEFAULT_ENCRYPTION_FIELD)
        )
        kr = get_keyring()
        fernet = kr.fernet_for_version(key_version)
        ct = fernet.encrypt(json.dumps(data_dict).encode())
        blob = _pack_header(key_version) + ct
        cr.execute(
            'INSERT INTO "{}" ("{}") VALUES (%s) RETURNING id'.format(
                self.TABLE, DEFAULT_ENCRYPTION_FIELD
            ),
            (blob,),
        )
        return cr.fetchone()[0]

    def _read_raw_blob(self, rec_id):
        cr = self.env.cr
        cr.execute(
            'SELECT "{}" FROM "{}" WHERE id = %s'.format(
                DEFAULT_ENCRYPTION_FIELD, self.TABLE
            ),
            (rec_id,),
        )
        row = cr.fetchone()
        return bytes(row[0]) if row and row[0] else None

    def test_cron_skips_single_key(self):
        os.environ[REC_ENCRYPTION_KEY.upper()] = self.k0
        reset_keyring()
        self.icp.set_param(ICP_ENCRYPTION_KEY_VERSION, '0')
        self.env['base']._cron_re_encrypt_fields()
        self.assertEqual(
            self.icp.get_param(ICP_ENCRYPTION_KEY_VERSION), '0',
        )

    def test_cron_skips_already_migrated(self):
        self.icp.set_param(ICP_ENCRYPTION_KEY_VERSION, '1')
        self.env['base']._cron_re_encrypt_fields()
        self.assertEqual(
            self.icp.get_param(ICP_ENCRYPTION_KEY_VERSION), '1',
        )

    def test_cron_stamps_version_when_no_tables(self):
        with patch.object(
            type(self.env['base']),
            '_find_encryption_tables',
            return_value=[],
        ):
            self.env['base']._cron_re_encrypt_fields()
        self.assertEqual(
            self.icp.get_param(ICP_ENCRYPTION_KEY_VERSION), '1',
        )

    def test_cron_re_encrypts_and_stamps(self):
        rid = self._create_test_table_with_blob({"secret": "cron_test"}, key_version=0)
        with patch.object(
            type(self.env['base']),
            '_find_encryption_tables',
            return_value=[(self.TABLE, DEFAULT_ENCRYPTION_FIELD)],
        ):
            self.env['base']._cron_re_encrypt_fields()
        raw = self._read_raw_blob(rid)
        ver, _ = _unpack_header(raw)
        self.assertEqual(ver, 1)
        self.assertEqual(
            self.icp.get_param(ICP_ENCRYPTION_KEY_VERSION), '1',
        )

    def test_cron_does_not_stamp_on_failure(self):
        self._create_test_table_with_blob({"secret": "fail_test"}, key_version=0)
        with patch.object(
            type(self.env['base']),
            '_find_encryption_tables',
            return_value=[(self.TABLE, DEFAULT_ENCRYPTION_FIELD)],
        ), patch(
            'odoo.addons.hibou_field_encryption.models.models.re_encrypt_table',
            side_effect=Exception("db error"),
        ):
            self.env['base']._cron_re_encrypt_fields()
        self.assertEqual(
            self.icp.get_param(ICP_ENCRYPTION_KEY_VERSION), '0',
        )

    def test_cron_no_keyring_gracefully_skips(self):
        os.environ.pop(REC_ENCRYPTION_KEY.upper(), None)
        reset_keyring()
        self.env['base']._cron_re_encrypt_fields()
        self.assertEqual(
            self.icp.get_param(ICP_ENCRYPTION_KEY_VERSION), '0',
        )

    def test_find_encryption_tables_discovers_fields(self):
        tables = self.env['base']._find_encryption_tables()
        self.assertIsInstance(tables, list)
        has_encryption = any(
            fname == DEFAULT_ENCRYPTION_FIELD
            for _table, fname in tables
        )
        if self.env.registry.models.get('enc.test.sugar'):
            self.assertTrue(has_encryption)
