import json
import os

from cryptography.fernet import Fernet

from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools.config import config

from odoo.addons.hibou_field_encryption.models.fields import (
    DEFAULT_ENCRYPTION_FIELD,
    Encryption,
    REC_ENCRYPTION_KEY,
    migrate_fields_to_encryption,
)

TEST_KEY = Fernet.generate_key().decode()


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
        setup_test_model(cls.env, [EncryptPartnerExplicit])

    @classmethod
    def tearDownClass(cls):
        os.environ.pop(REC_ENCRYPTION_KEY.upper(), None)
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
        setup_test_model(cls.env, [EncryptPartnerSugar])

    @classmethod
    def tearDownClass(cls):
        os.environ.pop(REC_ENCRYPTION_KEY.upper(), None)
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
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self._orig_config = config.options.get(REC_ENCRYPTION_KEY)
        self._orig_env = os.environ.get(REC_ENCRYPTION_KEY.upper())

    def tearDown(self):
        if self._orig_config is not None:
            config[REC_ENCRYPTION_KEY] = self._orig_config
        else:
            config.options.pop(REC_ENCRYPTION_KEY, None)
        if self._orig_env is not None:
            os.environ[REC_ENCRYPTION_KEY.upper()] = self._orig_env
        else:
            os.environ.pop(REC_ENCRYPTION_KEY.upper(), None)
        super().tearDown()

    def test_key_from_env_var(self):
        config.options.pop(REC_ENCRYPTION_KEY, None)
        os.environ[REC_ENCRYPTION_KEY.upper()] = TEST_KEY
        enc = Encryption()
        cipher = enc._get_cipher()
        data = b"test data"
        encrypted = cipher.encrypt(data)
        self.assertEqual(cipher.decrypt(encrypted), data)

    def test_key_from_config(self):
        os.environ.pop(REC_ENCRYPTION_KEY.upper(), None)
        config[REC_ENCRYPTION_KEY] = TEST_KEY
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
        enc = Encryption()
        cipher = enc._get_cipher()
        test_cipher = Fernet(key1.encode())
        data = b"precedence test"
        encrypted = cipher.encrypt(data)
        self.assertEqual(test_cipher.decrypt(encrypted), data)

    def test_no_key_raises_error(self):
        config.options.pop(REC_ENCRYPTION_KEY, None)
        os.environ.pop(REC_ENCRYPTION_KEY.upper(), None)
        enc = Encryption()
        with self.assertRaises(ValidationError):
            enc._get_cipher()


@tagged("post_install", "-at_install")
class TestMigrateFieldsToEncryption(TransactionCase):
    TABLE = "test_enc_migration"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.environ[REC_ENCRYPTION_KEY.upper()] = TEST_KEY

    @classmethod
    def tearDownClass(cls):
        os.environ.pop(REC_ENCRYPTION_KEY.upper(), None)
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
