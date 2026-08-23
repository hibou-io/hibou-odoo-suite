import json
import os
from unittest.mock import patch

from cryptography.fernet import Fernet

from odoo.exceptions import ValidationError, UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools.config import config

from odoo.addons.hibou_field_encryption.models.fields import (
    DEFAULT_ENCRYPTION_FIELD,
    DecryptFailed,
    Encryption,
    EncryptionKeyring,
    UndecryptableData,
    GCP_PROJECT,
    GCP_SECRET_NAME,
    REC_ENCRYPTION_DISABLE_AUTO_REENCRYPT,
    REC_ENCRYPTION_KEY,
    REC_ENCRYPTION_KEY_PATH,
    REC_ENCRYPTION_KEY_PROVIDER,
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
    REC_ENCRYPTION_KEY_PATH,
    REC_ENCRYPTION_KEY_PROVIDER,
    REC_ENCRYPTION_DISABLE_AUTO_REENCRYPT,
    GCP_PROJECT,
    GCP_SECRET_NAME,
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

    def _revoked_key_blob(self):
        """A blob whose key version is not in the configured keyring."""
        k1 = Fernet.generate_key().decode()
        k2 = Fernet.generate_key().decode()
        revoked = Fernet.generate_key().decode()
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"1:{k1},2:{k2}"
        reset_keyring()
        ct = Fernet(revoked.encode()).encrypt(b'{"gone": true}')
        return _pack_header(99) + ct

    def test_decrypt_revoked_key_raises(self):
        """_decrypt_data reports failure rather than reporting emptiness.

        An empty blob and an unreadable blob must not look alike: the first
        means nothing was stored, the second means something was and we cannot
        read it. Conflating them is what allowed a write to overwrite data it
        had failed to decrypt.
        """
        blob = self._revoked_key_blob()
        enc = Encryption()
        enc.name = "test_field"
        with self.assertRaises(DecryptFailed) as caught:
            enc._decrypt_data(blob)
        self.assertEqual(caught.exception.key_version, 99)

    def test_convert_to_record_revoked_key_degrades_to_marker(self):
        """Reads stay tolerant, but the result is flagged as unreadable."""
        blob = self._revoked_key_blob()
        enc = Encryption()
        enc.name = "test_field"
        enc.model_name = "test.model"
        result = enc.convert_to_record(blob, None)
        self.assertEqual(result, {})
        self.assertIsInstance(result, UndecryptableData)

    def test_convert_to_record_empty_is_not_a_marker(self):
        """A genuinely empty blob is ordinary empty data, and stays writable.

        This is the case a neutralized database is in, so it must not be
        confused with an unreadable one.
        """
        enc = Encryption()
        enc.name = "test_field"
        self.assertEqual(enc.convert_to_record(None, None), {})
        self.assertNotIsInstance(enc.convert_to_record(None, None), UndecryptableData)


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
class TestWriteAfterFailedDecrypt(TransactionCase):
    """Writing one encrypt field must not silently discard its siblings.

    Both fields share a single blob. If that blob cannot be decrypted, a write
    used to persist a dict containing only the field being written, wiping the
    other one permanently -- recovering the key afterwards would not bring it
    back, because the ciphertext was gone.
    """

    def setUp(self):
        super().setUp()
        self._saved = _save_and_clear(*ALL_CONFIG_KEYS)
        self.k0 = Fernet.generate_key().decode()
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"0:{self.k0}"
        reset_keyring()
        self.record = self.env["enc.test.sugar"].create({
            "name": "subject",
            "secret_one": "one",
            "secret_two": "two",
        })
        self.env.flush_all()

    def tearDown(self):
        _restore(self._saved)
        reset_keyring()
        super().tearDown()

    def _revoke_key(self):
        """Swap in a keyring that cannot read what was already written."""
        replacement = Fernet.generate_key().decode()
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"7:{replacement}"
        reset_keyring()
        self.record.invalidate_recordset()

    def test_read_degrades_to_empty(self):
        self._revoke_key()
        self.assertFalse(self.record.secret_one)
        self.assertFalse(self.record.secret_two)

    def test_write_is_refused(self):
        self._revoke_key()
        with self.assertRaises(UserError):
            self.record.secret_one = "replacement"
            self.env.flush_all()

    def test_siblings_survive_a_refused_write(self):
        self._revoke_key()
        # A savepoint, not cr.rollback(): rolling the test's own cursor back
        # breaks it for the rest of the case.
        with self.assertRaises(UserError):
            with self.env.cr.savepoint():
                self.record.secret_one = "replacement"
                self.env.flush_all()
        # Drop the rejected write from the cache without flushing it.
        self.env.invalidate_all(flush=False)

        # With the original key back, both values must still be there.
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"0:{self.k0}"
        reset_keyring()
        self.assertEqual(self.record.secret_one, "one")
        self.assertEqual(self.record.secret_two, "two")

    def test_write_still_works_when_readable(self):
        self.record.secret_one = "changed"
        self.env.flush_all()
        self.record.invalidate_recordset()
        self.assertEqual(self.record.secret_one, "changed")
        self.assertEqual(self.record.secret_two, "two")


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

    def _insert_poison_blob(self):
        """A row whose key version is not in the keyring at all."""
        stranger = Fernet.generate_key()
        ct = Fernet(stranger).encrypt(b'{"unreadable": true}')
        blob = _pack_header(42) + ct
        cr = self.env.cr
        cr.execute(
            'INSERT INTO "{}" ("{}") VALUES (%s) RETURNING id'.format(
                self.TABLE, DEFAULT_ENCRYPTION_FIELD
            ),
            (blob,),
        )
        return cr.fetchone()[0]

    def test_poison_row_does_not_stall_the_table(self):
        """One unreadable row must not stop the rest from rotating.

        Aborting the table left the rotation permanently stuck with no way to
        tell which row was at fault.
        """
        good = self._insert_blob({"a": "1"}, key_version=0)
        poison = self._insert_poison_blob()
        after = self._insert_blob({"b": "2"}, key_version=0)

        updated = re_encrypt_table(self.env.cr, self.TABLE)

        self.assertEqual(updated, 2)
        for rec_id in (good, after):
            version, _ct = _unpack_header(self._read_raw_blob(rec_id))
            self.assertEqual(version, 1)
        # left alone, so the histogram still reports it and no key can be retired
        version, _ct = _unpack_header(self._read_raw_blob(poison))
        self.assertEqual(version, 42)

    def test_migrate_aborts_on_unreadable_blob(self):
        """A migration must not merge plaintext into a blob it could not read."""
        cr = self.env.cr
        cr.execute('ALTER TABLE "{}" ADD COLUMN "plain_col" varchar'.format(self.TABLE))
        rec_id = self._insert_poison_blob()
        cr.execute(
            'UPDATE "{}" SET "plain_col" = %s WHERE id = %s'.format(self.TABLE),
            ("incoming", rec_id),
        )

        with self.assertRaises(UserError):
            migrate_fields_to_encryption(cr, self.TABLE, ["plain_col"])

        # the unreadable blob is untouched, so the data is still recoverable
        version, _ct = _unpack_header(self._read_raw_blob(rec_id))
        self.assertEqual(version, 42)

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
        # Without the patch this raises UserError for the missing library on
        # hosts where google-cloud-secret-manager is not installed, which is
        # not what this test is about (ValidationError subclasses UserError,
        # so assertRaises would not catch it either).
        with patch(
            "odoo.addons.hibou_field_encryption.models.fields.secretmanager"
        ), self.assertRaises(ValidationError):
            get_keyring()

    def test_gcp_provider_missing_secret_raises(self):
        os.environ[REC_ENCRYPTION_KEY_PROVIDER.upper()] = "gcp_secret_manager"
        os.environ[GCP_PROJECT.upper()] = "some-project"
        reset_keyring()
        with patch(
            "odoo.addons.hibou_field_encryption.models.fields.secretmanager"
        ), self.assertRaises(ValidationError):
            get_keyring()

    def test_gcp_missing_library_raises(self):
        os.environ[REC_ENCRYPTION_KEY_PROVIDER.upper()] = "gcp_secret_manager"
        os.environ[GCP_PROJECT.upper()] = "some-project"
        os.environ[GCP_SECRET_NAME.upper()] = "some-secret"
        reset_keyring()
        with patch(
            "odoo.addons.hibou_field_encryption.models.fields.secretmanager",
            None,
        ), self.assertRaises(UserError):
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
        # The cron commits each batch; Odoo forbids a real commit inside a test.
        with patch.object(
            type(self.env['base']),
            '_find_encryption_tables',
            return_value=[(self.TABLE, DEFAULT_ENCRYPTION_FIELD)],
        ), patch.object(self.env.cr, 'commit'):
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
        """Discovery reports columns that exist. A model can be in the registry
        without its table being in the database (test models built in a rolled
        back transaction), so presence in the registry alone is not enough.
        """
        self._create_test_table_with_blob({"secret": "discover"}, key_version=0)
        tables = self.env['base']._find_encryption_tables()
        self.assertIsInstance(tables, list)
        self.assertIn((self.TABLE, DEFAULT_ENCRYPTION_FIELD), tables)

    def test_cron_skips_when_auto_reencrypt_disabled(self):
        rid = self._create_test_table_with_blob({"secret": "keep"}, key_version=0)
        os.environ[REC_ENCRYPTION_DISABLE_AUTO_REENCRYPT.upper()] = '1'
        with patch.object(
            type(self.env['base']),
            '_find_encryption_tables',
            return_value=[(self.TABLE, DEFAULT_ENCRYPTION_FIELD)],
        ):
            self.env['base']._cron_re_encrypt_fields()
        ver, _ = _unpack_header(self._read_raw_blob(rid))
        self.assertEqual(ver, 0)
        self.assertEqual(self.icp.get_param(ICP_ENCRYPTION_KEY_VERSION), '0')

































