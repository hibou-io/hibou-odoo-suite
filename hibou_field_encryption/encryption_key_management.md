# Encryption Key Management for `hibou_field_encryption`

## Overview

The `hibou_field_encryption` module encrypts sensitive field values at rest in
PostgreSQL using Fernet symmetric encryption (from the `cryptography` library).
It supports a **versioned keyring** so that you can rotate encryption keys
without downtime and without losing access to data encrypted with older keys.

Keys can be loaded from:

- **Config / environment variables** — simple, no external dependencies.
- **Google Cloud Secret Manager** — managed key lifecycle, audit logging,
  automatic version-to-keyring mapping.

---

## Quick Start — Single Key (Config Provider)

Generate a key:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Example output:

```
bN3xG7z9Q1kFmTv8sJpL2wYdAeRcUhKi0oNfVgXjZq4=
```

Set it in your Odoo config file:

```ini
[options]
rec_encryption_key = bN3xG7z9Q1kFmTv8sJpL2wYdAeRcUhKi0oNfVgXjZq4=
```

Or via environment variable:

```bash
export REC_ENCRYPTION_KEY=bN3xG7z9Q1kFmTv8sJpL2wYdAeRcUhKi0oNfVgXjZq4=
```

Restart Odoo. All `encrypt=True` fields will now be encrypted with this key.

---

## Key Providers

The key provider determines **where** the keyring is loaded from. Set it via
`rec_encryption_key_provider` in the config file or the
`REC_ENCRYPTION_KEY_PROVIDER` environment variable.

| Provider | Value | Description |
|---|---|---|
| Config / env | `config` (default) | Keys inline in config or env vars |
| GCP Secret Manager | `gcp_secret_manager` | Keys from a GCP secret, one Fernet key per version |

If not set, the provider defaults to `config`.

---

## Config Provider

This is the default. No additional dependencies required beyond `cryptography`.

### Single-Key Format

```
rec_encryption_key = <base64-fernet-key>
```

Treated as key version `0`.

### Multi-Key Format (for rotation)

```
rec_encryption_key = 0:<key0>,1:<key1>,2:<key2>
```

- Comma-separated `version:key` pairs.
- Versions are integers (0–65535).
- The **highest version** is the current encryption key.
- Whitespace around commas, colons, and keys is ignored.

---

## GCP Secret Manager Provider

Use Google Cloud Secret Manager to store and manage your Fernet keys. Each
**enabled version** of a GCP secret becomes a key in the keyring. The GCP
version number maps directly to the keyring version number. The latest (highest)
enabled version is the current encryption key.

### Prerequisites

```bash
pip install google-cloud-secret-manager
```

Authentication uses
[Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials).
In GKE/Cloud Run this is automatic. Locally, run:

```bash
gcloud auth application-default login
```

Or set a service account key:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### Configuration

```ini
[options]
rec_encryption_key_provider = gcp_secret_manager
rec_encryption_gcp_project = my-gcp-project
rec_encryption_gcp_secret = odoo-encryption-key
```

Or via environment variables:

```bash
export REC_ENCRYPTION_KEY_PROVIDER=gcp_secret_manager
export REC_ENCRYPTION_GCP_PROJECT=my-gcp-project
export REC_ENCRYPTION_GCP_SECRET=odoo-encryption-key
```

### Initial Setup

#### 1. Create the GCP Secret

```bash
gcloud secrets create odoo-encryption-key \
    --project=my-gcp-project \
    --replication-policy=automatic
```

#### 2. Add the First Key Version

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" \
    | gcloud secrets versions add odoo-encryption-key \
        --project=my-gcp-project \
        --data-file=-
```

This creates version `1`. Verify:

```bash
gcloud secrets versions list odoo-encryption-key --project=my-gcp-project
```

#### 3. Configure Odoo and Restart

```bash
export REC_ENCRYPTION_KEY_PROVIDER=gcp_secret_manager
export REC_ENCRYPTION_GCP_PROJECT=my-gcp-project
export REC_ENCRYPTION_GCP_SECRET=odoo-encryption-key
```

On startup, the module fetches all enabled versions, builds the keyring, and
logs:

```
Loaded encryption keyring from GCP Secret Manager: 1 key(s), current version 1.
```

### Key Rotation with GCP

#### 1. Add a New Version

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" \
    | gcloud secrets versions add odoo-encryption-key \
        --project=my-gcp-project \
        --data-file=-
```

This creates version `2` (or the next sequential number).

#### 2. Restart Odoo

The keyring now has both versions. New writes use version `2`; old data
decrypts with version `1`.

#### 3. Re-encrypt Existing Data

```python
from odoo.addons.hibou_field_encryption.models.fields import re_encrypt_table

re_encrypt_table(env.cr, 'eyrie_datasource')
re_encrypt_table(env.cr, 'eyrie_webhook')
re_encrypt_table(env.cr, 'res_partner')
env.cr.commit()
```

#### 4. Disable the Old Version (Optional)

Once all data is re-encrypted to version `2`:

```bash
gcloud secrets versions disable 1 \
    --secret=odoo-encryption-key \
    --project=my-gcp-project
```

After the next Odoo restart, the keyring will only contain version `2`.
Disabled versions are excluded from the `state:ENABLED` filter.

> **Warning**: If any row is still encrypted with version `1` when you disable
> it, that data becomes **unreadable**. Always verify re-encryption is complete
> first.

#### 5. Destroy the Old Version (Permanent)

```bash
gcloud secrets versions destroy 1 \
    --secret=odoo-encryption-key \
    --project=my-gcp-project
```

This is irreversible. The key material is permanently deleted from GCP.

### GCP IAM Permissions

The service account running Odoo needs:

| Permission | Role |
|---|---|
| `secretmanager.versions.list` | `roles/secretmanager.viewer` |
| `secretmanager.versions.access` | `roles/secretmanager.secretAccessor` |

For the narrowest scope, create a custom role with just these two permissions
and bind it to the specific secret.

---

## Key Rotation (Config Provider)

### Step-by-Step

#### 1. Generate a New Key

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

#### 2. Update Configuration to a Multi-Key Keyring

```ini
[options]
rec_encryption_key = 0:<original_key>,1:<new_key>
```

Or:

```bash
export REC_ENCRYPTION_KEY="0:<original_key>,1:<new_key>"
```

#### 3. Restart Odoo

- **New writes** are encrypted with key version `1`.
- **Old reads** transparently decrypt using key version `0`.
- No downtime, no data loss.

#### 4. Re-encrypt Existing Data

```python
from odoo.addons.hibou_field_encryption.models.fields import re_encrypt_table

re_encrypt_table(env.cr, 'eyrie_datasource')
re_encrypt_table(env.cr, 'eyrie_webhook')
re_encrypt_table(env.cr, 'res_partner')
env.cr.commit()
```

`re_encrypt_table()` returns the number of rows that were actually updated:

```python
updated = re_encrypt_table(env.cr, 'eyrie_datasource')
print(f"Re-encrypted {updated} rows in eyrie_datasource")
```

For a custom encryption field name:

```python
re_encrypt_table(env.cr, 'my_table', encryption_field='my_custom_enc')
```

You can also re-encrypt individual blobs programmatically:

```python
from odoo.addons.hibou_field_encryption.models.fields import re_encrypt_blob

changed, new_blob = re_encrypt_blob(old_blob)
if changed:
    # new_blob is encrypted with the current key version
    ...
```

#### 5. Remove the Old Key

Once **all** rows in **all** tables have been re-encrypted:

```ini
[options]
rec_encryption_key = 1:<new_key>
```

> **Warning**: If any row is still encrypted with the removed version, that data
> will be **permanently unreadable**.

#### 6. Subsequent Rotations

```bash
# Second rotation
export REC_ENCRYPTION_KEY="1:<key1>,2:<key2>"

# Third rotation
export REC_ENCRYPTION_KEY="2:<key2>,3:<key3>"
```

---

## Configuration Reference

| Config Key | Environment Variable | Default | Description |
|---|---|---|---|
| `rec_encryption_key_provider` | `REC_ENCRYPTION_KEY_PROVIDER` | `config` | Key provider: `config` or `gcp_secret_manager` |
| `rec_encryption_key` | `REC_ENCRYPTION_KEY` | *(required for config provider)* | Single Fernet key or versioned keyring |
| `rec_encryption_gcp_project` | `REC_ENCRYPTION_GCP_PROJECT` | *(required for gcp)* | GCP project ID |
| `rec_encryption_gcp_secret` | `REC_ENCRYPTION_GCP_SECRET` | *(required for gcp)* | GCP secret name |

The Odoo config file takes precedence over environment variables when both are
set.

---

## Wire Format

Each encrypted blob stored in PostgreSQL has this structure:

```
┌──────────┬──────────────┬─────────────────────────────────┐
│  1 byte  │   2 bytes    │         variable length         │
│  0x01    │  key version │       Fernet ciphertext         │
│ (format) │ (big-endian) │                                 │
└──────────┴──────────────┴─────────────────────────────────┘
```

- **Format byte** (`0x01`): Identifies this as a versioned blob.
- **Key version** (uint16 big-endian): Which key in the keyring encrypted this
  blob.
- **Fernet ciphertext**: The encrypted payload.

Legacy blobs (written before the keyring feature) have no header — they start
directly with the Fernet token (`gAAAAA...`). These are detected automatically
and decrypted with key version `0`.

---

## Discovering Tables with Encrypted Fields

To find which tables need re-encryption after a key rotation, query for columns
of the encryption field type:

```sql
SELECT table_name, column_name
FROM information_schema.columns
WHERE column_name = 'rec_encrypted'
   OR column_name LIKE '%_encrypted'
ORDER BY table_name;
```

Or inspect the Odoo registry from a shell:

```python
for model_name, Model in env.registry.models.items():
    for fname, field in Model._fields.items():
        if field.type == 'encryption':
            table = Model._table
            print(f"{table}.{fname}")
```

---

## Migrating from Config Provider to GCP

If you are already running with the `config` provider and want to switch to GCP:

1. **Create the GCP secret** and add your current key as version `1`:

   ```bash
   echo -n "<your-current-fernet-key>" \
       | gcloud secrets create odoo-encryption-key \
           --project=my-gcp-project \
           --replication-policy=automatic \
           --data-file=-
   ```

2. **Switch the provider** in your config:

   ```bash
   export REC_ENCRYPTION_KEY_PROVIDER=gcp_secret_manager
   export REC_ENCRYPTION_GCP_PROJECT=my-gcp-project
   export REC_ENCRYPTION_GCP_SECRET=odoo-encryption-key
   ```

3. **Restart Odoo**. The module loads the same key from GCP (version `1`)
   instead of the config string.

4. **Important**: If your existing data was written with the config provider
   (key version `0` in the blob headers), and GCP loads it as version `1`, you
   need to re-encrypt all data so the version headers match:

   ```python
   from odoo.addons.hibou_field_encryption.models.fields import re_encrypt_table
   re_encrypt_table(env.cr, 'eyrie_datasource')
   # ... all other tables
   env.cr.commit()
   ```

5. Remove the old `REC_ENCRYPTION_KEY` from your config/env. It is no longer
   used.

Future rotations are handled entirely in GCP — just add new secret versions and
restart.

---

## Troubleshooting

### "No 'rec_encryption_key' entry found"

The config provider cannot find a key. Ensure `rec_encryption_key` is set in
the Odoo config file **or** the `REC_ENCRYPTION_KEY` environment variable.

### "has been encrypted with a different key"

The blob was encrypted with a key that is not in the current keyring. This
happens when:

- A key was removed from the keyring before all data was re-encrypted.
- The `REC_ENCRYPTION_KEY` value was changed without preserving the old key.
- A GCP secret version was disabled/destroyed prematurely.

Recovery requires the original key. Add it back to the keyring (re-enable the
GCP version, or add it back to the config string).

### "encrypted with revoked key version X"

The blob carries a version header, but that version is not present in the
keyring. Add the key back for that version or accept that the data is
unreadable.

### "Unknown encryption key provider"

The `rec_encryption_key_provider` value is not `config` or
`gcp_secret_manager`. Check for typos.

### "No valid Fernet keys found in GCP secret"

The GCP secret exists but none of its enabled versions contain a valid Fernet
key. Verify the secret values are base64-encoded Fernet keys (44 characters,
ending with `=`).

### "Invalid key version 'X' in keyring configuration"

The version identifier in the multi-key config string is not a valid integer.
Check for typos in the `REC_ENCRYPTION_KEY` value.

### "The library 'cryptography' is missing"

```bash
pip install cryptography
```

### "The library 'google-cloud-secret-manager' is missing"

```bash
pip install google-cloud-secret-manager
```

---

## Security Considerations

- **Config provider**: Fernet keys live in plaintext in the config file or
  environment variables. Protect access with filesystem permissions, container
  secrets, or a secrets manager that injects them at runtime.
- **GCP provider**: Keys are stored in Google Cloud Secret Manager, which
  provides encryption at rest, IAM access controls, and audit logging. The keys
  are fetched once at startup and cached in process memory.
- **Memory**: Once loaded, the keyring lives in the Odoo worker process memory.
  This is the same security posture regardless of provider.
- **Database backups**: Encrypted blobs in PostgreSQL backups are only readable
  with the corresponding keys. Keep key backups separate from database backups.
- **Key version limits**: The wire format supports up to 65,535 key versions
  (uint16). In practice, you will never approach this limit.
- **GCP version numbers**: GCP Secret Manager assigns sequential integer
  version numbers starting at `1`. These map directly to keyring versions. If
  you disable and re-enable versions out of order, the keyring still picks the
  highest enabled version as current.
