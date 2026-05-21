import logging

from odoo import api, models, fields

from .fields import (
    get_keyring,
    re_encrypt_table,
    reset_keyring,
)

_logger = logging.getLogger(__name__)

ENCRYPTION_SUPPORTED_FIELD_TYPES = ["char", "text", "html", "selection"]
ICP_ENCRYPTION_KEY_VERSION = "encryption.migrated_key_version"


class Base(models.AbstractModel):
    _inherit = 'base'

    def _valid_field_parameter(self, field, name):
        return (name == 'encrypt' and field.type in ENCRYPTION_SUPPORTED_FIELD_TYPES) or super()._valid_field_parameter(field, name)

    @api.model
    def _find_encryption_tables(self):
        """Discover all (table, field_name) pairs with encryption fields
        by introspecting the registry.
        """
        result = []
        for model_name, Model in self.env.registry.models.items():
            for fname, field in Model._fields.items():
                if field.type == 'encryption':
                    result.append((Model._table, fname))
        return result

    @api.model
    def _cron_re_encrypt_fields(self):
        """Cron job: if the keyring has more than one version, re-encrypt
        all tables to the current version, then stamp a system parameter
        so we don't repeat the work.
        """
        try:
            reset_keyring()
            keyring = get_keyring()
        except Exception:
            _logger.debug(
                "Encryption keyring not available, skipping re-encryption cron."
            )
            return

        current = keyring.current_version
        if len(keyring) <= 1:
            return

        icp = self.env['ir.config_parameter'].sudo()
        migrated_str = icp.get_param(ICP_ENCRYPTION_KEY_VERSION, '0')
        try:
            migrated_version = int(migrated_str)
        except (ValueError, TypeError):
            migrated_version = 0

        if migrated_version >= current:
            return

        tables = self._find_encryption_tables()
        if not tables:
            icp.set_param(ICP_ENCRYPTION_KEY_VERSION, str(current))
            return

        total_updated = 0
        cr = self.env.cr
        for table, enc_field in tables:
            try:
                updated = re_encrypt_table(cr, table, encryption_field=enc_field)
                if updated:
                    _logger.info(
                        "Re-encrypted %d rows in %s.%s to key version %d.",
                        updated, table, enc_field, current,
                    )
                    total_updated += updated
            except Exception:
                _logger.exception(
                    "Failed to re-encrypt %s.%s, will retry next run.",
                    table, enc_field,
                )
                return

        icp.set_param(ICP_ENCRYPTION_KEY_VERSION, str(current))
        _logger.info(
            "Encryption key rotation complete: %d rows re-encrypted to version %d.",
            total_updated, current,
        )


class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'

    ttype = fields.Selection(selection_add=[('encryption', 'encryption')], ondelete={'encryption': 'cascade'})
