import logging
import time

from odoo import api, models, fields

from .fields import (
    EXTERNALLY_MANAGED_PROVIDERS,
    REC_ENCRYPTION_DISABLE_AUTO_REENCRYPT,
    auto_reencrypt_disabled,
    current_key_provider,
    find_encryption_columns,
    get_keyring,
    pending_re_encrypt_count,
    re_encrypt_table,
    reload_keyring,
    reset_keyring,
    set_keyring,
)

_logger = logging.getLogger(__name__)

ENCRYPTION_SUPPORTED_FIELD_TYPES = ["char", "text", "html", "selection"]
ICP_ENCRYPTION_KEY_VERSION = "encryption.migrated_key_version"

# Arbitrary but stable key so that only one worker performs the automatic
# re-encryption while the others move on.
REENCRYPT_LOCK_KEY = 0x48464531

# Wall-clock budget for one cron pass. The cron runs against a live system, so
# it does as much as it can within this budget and resumes on the next run
# rather than holding a long transaction.
REENCRYPT_CRON_TIME_BUDGET = 300


class Base(models.AbstractModel):
    _inherit = 'base'

    def _valid_field_parameter(self, field, name):
        return (name == 'encrypt' and field.type in ENCRYPTION_SUPPORTED_FIELD_TYPES) or super()._valid_field_parameter(field, name)

    @api.model
    def _find_encryption_tables(self):
        """Discover all (table, field_name) pairs with encryption fields
        by introspecting the registry and the database catalog.
        """
        return find_encryption_columns(self.env.cr, registry=self.env.registry)

    @api.model
    def _encryption_migrated_version(self):
        icp = self.env['ir.config_parameter'].sudo()
        try:
            return int(icp.get_param(ICP_ENCRYPTION_KEY_VERSION, '0'))
        except (ValueError, TypeError):
            return 0

    @api.model
    def _encryption_rotation_pending(self):
        """Return the current key version when a rotation is outstanding,
        otherwise ``None``.

        Reads this process's keyring as-is. Re-reading the key source here
        would put whichever process asked ahead of the rest of the fleet.
        """
        try:
            keyring = get_keyring()
        except Exception:
            _logger.debug("Encryption keyring not available, skipping re-encryption.")
            return None

        if len(keyring) <= 1:
            return None

        current = keyring.current_version
        if self._encryption_migrated_version() >= current:
            return None
        return current

    @api.model
    def _re_encrypt_to_current_version(self, current, incremental=False):
        """Re-encrypt every discovered encryption column to *current*.

        With *incremental* (the cron), the pass is co-operative: it skips rows
        another transaction is writing, commits each batch so it never holds a
        long transaction, gives up its advisory lock between batches, and stops
        after ``REENCRYPT_CRON_TIME_BUDGET`` seconds. Whatever is left is picked
        up by the next run, because each blob records its own key version.

        The migrated version is only stamped once no row is left behind, so the
        stamp can be trusted before retiring a key.

        Returns True when the rotation is complete and stamped.
        """
        icp = self.env['ir.config_parameter'].sudo()
        columns = self._find_encryption_tables()
        if not columns:
            icp.set_param(ICP_ENCRYPTION_KEY_VERSION, str(current))
            return True

        deadline = None
        lock_check = None
        if incremental:
            deadline = time.monotonic() + REENCRYPT_CRON_TIME_BUDGET
            lock_check = self._try_re_encrypt_lock

        total_updated = 0
        for table, enc_field in columns:
            try:
                updated = re_encrypt_table(
                    self.env.cr, table, encryption_field=enc_field,
                    skip_locked=incremental, commit=incremental,
                    deadline=deadline, lock_check=lock_check,
                )
            except Exception:
                _logger.exception(
                    "Failed to re-encrypt %s.%s, will retry next run.",
                    table, enc_field,
                )
                return False
            if updated:
                _logger.info(
                    "Re-encrypted %d rows in %s.%s to key version %d.",
                    updated, table, enc_field, current,
                )
                total_updated += updated

        # Verified on every path, not just the incremental one: a worker
        # holding an older cached keyring can write a stale row while the pass
        # runs, and stamping over that would declare the retired key safe to
        # delete while data still needs it.
        remaining = sum(
            pending_re_encrypt_count(self.env.cr, table, enc_field)
            for table, enc_field in columns
        )

        if remaining:
            _logger.info(
                "Re-encrypted %d rows to key version %d; %d row(s) still pending, "
                "continuing on the next run.",
                total_updated, current, remaining,
            )
            return False

        icp.set_param(ICP_ENCRYPTION_KEY_VERSION, str(current))
        _logger.info(
            "Encryption key rotation complete: %d rows re-encrypted to version %d.",
            total_updated, current,
        )
        return True

    @api.model
    def _signal_registry_change(self):
        """Tell every other worker to rebuild its registry.

        That is what makes them re-read the key source, since the keyring is
        refreshed at registry load. Returns False if signalling is unavailable,
        so the caller can decline to move ahead of the fleet.
        """
        try:
            registry = self.env.registry
            registry.registry_invalidated = True
            registry.signal_changes()
            return True
        except Exception:
            _logger.exception(
                "Could not signal the registry, so other workers would keep "
                "their current keyring."
            )
            return False

    @api.model
    def _poll_key_source(self):
        """Re-read an externally managed key source and publish any change.

        Only providers whose key set can change without a restart are polled.
        When the set of key versions has changed, every worker is told to
        rebuild so the whole fleet moves to the new keyring together.

        Re-encryption is deliberately left to the *next* run: rotating now
        would rewrite rows to a version the other workers are not writing yet.

        Returns True when a change was published.
        """
        if current_key_provider() not in EXTERNALLY_MANAGED_PROVIDERS:
            return False

        try:
            previous = get_keyring()
            before = tuple(previous.versions)
        except Exception:
            previous, before = None, ()

        try:
            after = tuple(reload_keyring().versions)
        except Exception:
            _logger.exception(
                "Could not re-read the encryption key source; keeping the "
                "keyring this process already has."
            )
            return False

        if after == before:
            return False

        if not self._signal_registry_change():
            # Stay on the old keyring rather than becoming the only process
            # that knows about the new one.
            set_keyring(previous)
            return False

        _logger.warning(
            "Encryption key versions changed from %s to %s. Every worker has "
            "been signalled to reload; re-encryption starts on the next run.",
            list(before), list(after),
        )
        return True

    @api.model
    def _try_re_encrypt_lock(self):
        """Take a transaction-level advisory lock so that only one worker
        performs the rewrite. Returns False when another process holds it.
        """
        self.env.cr.execute(
            "SELECT pg_try_advisory_xact_lock(%s)", (REENCRYPT_LOCK_KEY,),
        )
        return bool(self.env.cr.fetchone()[0])

    @api.model
    def _re_encrypt_now(self):
        """Manual entry point: re-encrypt everything to the current key version.

        Ignores ``rec_encryption_disable_auto_reencrypt``, so this is what you
        call from ``odoo shell`` or a server action when automatic rotation is
        turned off::

            env['base']._re_encrypt_now()
            env.cr.commit()

        Returns True when nothing is pending or the pass succeeded.
        """
        current = self._encryption_rotation_pending()
        if current is None:
            _logger.info("No encryption key rotation pending.")
            return True
        return self._re_encrypt_to_current_version(current)

    @api.model
    def _cron_re_encrypt_fields(self):
        """Cron job: catch up any rows that the startup pass did not convert
        (for example because it failed part-way, or a new database was
        restored after the keyring already had several versions).

        Runs incrementally so it can share the database with live traffic.
        """
        if auto_reencrypt_disabled():
            _logger.info(
                "Automatic re-encryption is disabled by '%s', skipping cron.",
                REC_ENCRYPTION_DISABLE_AUTO_REENCRYPT,
            )
            return

        if self._poll_key_source():
            return

        current = self._encryption_rotation_pending()
        if current is None:
            return
        self._re_encrypt_to_current_version(current, incremental=True)

    @api.model
    def _auto_re_encrypt_fields(self):
        """Re-encrypt to the current key version at registry load.

        Called once per registry load from ``IrModelFields._register_hook``.
        Runs by default whenever the keyring holds more than one key version
        and the database has not been stamped with that version yet. Adding a
        new key version and restarting is therefore all a rotation requires.

        The pass is blocking: the instance does not serve requests until it
        finishes. If it turns out to be too slow, set
        ``rec_encryption_disable_auto_reencrypt`` and use
        ``env['base']._re_encrypt_now()`` during a maintenance window instead.
        """
        if auto_reencrypt_disabled():
            _logger.info(
                "Automatic re-encryption is disabled by '%s'. Rotate manually "
                "with env['base']._re_encrypt_now().",
                REC_ENCRYPTION_DISABLE_AUTO_REENCRYPT,
            )
            return

        # Registry load is the only moment every process re-reads the key
        # source, so the whole fleet converges on the same keyring. The cron
        # deliberately does not do this: it is a single process, and a key
        # version only it knows about would be rotated to while every HTTP
        # worker kept writing with the old one.
        reset_keyring()

        current = self._encryption_rotation_pending()
        if current is None:
            return

        if not self._try_re_encrypt_lock():
            _logger.info(
                "Re-encryption is already running in another process, "
                "skipping in this one."
            )
            return

        cr = self.env.cr

        _logger.warning(
            "Encryption key rotation to version %d detected. Re-encrypting all "
            "encrypted fields now; this instance will NOT serve requests until "
            "it finishes. Set '%s' to disable this and rotate manually.",
            current, REC_ENCRYPTION_DISABLE_AUTO_REENCRYPT,
        )
        started = time.time()
        if self._re_encrypt_to_current_version(current):
            cr.commit()
            _logger.warning(
                "Re-encryption to key version %d finished in %.1fs. The retired "
                "key can be removed from the configuration once every database "
                "(including restored backups) has been re-encrypted.",
                current, time.time() - started,
            )


class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'

    ttype = fields.Selection(selection_add=[('encryption', 'encryption')], ondelete={'encryption': 'cascade'})

    def _register_hook(self):
        # Hooked on a single concrete model on purpose: _register_hook() runs
        # for every model in the registry, which would reload the keyring (and,
        # with the GCP provider, call Secret Manager) once per model.
        res = super()._register_hook()
        try:
            self.env['base']._auto_re_encrypt_fields()
        except Exception:
            _logger.exception(
                "Automatic re-encryption failed. The keyring still decrypts old "
                "data, so the instance remains usable; the cron will retry."
            )
        return res
