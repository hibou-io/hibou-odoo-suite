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
| File | `file` | Keys from a file on disk, supplied by anything |
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
- A single versioned entry is also valid (`rec_encryption_key = 2:<key2>`).

### Recycling a Simple (Unversioned) Key

A bare `rec_encryption_key` is loaded as version `0`, and blobs written without
a version header are also assumed to be version `0`. So an existing simple key
needs no data migration to become rotatable — just give it its version number
explicitly and append the new key:

```bash
# before
export REC_ENCRYPTION_KEY="<original_key>"

# after
export REC_ENCRYPTION_KEY="0:<original_key>,1:<new_key>"
```

Restart. The rotation is detected and performed automatically; see
[Automatic Re-encryption](#automatic-re-encryption).

---

## File Provider

Reads the keyring from a file. This is the portable option: anything that can
put a file on disk can supply the keys — a mounted Kubernetes secret, a CSI
driver for AWS/Azure/GCP, a Vault Agent template, `sops -d` at deploy time, or
plain configuration management. No extra Python dependency, and switching
backends later does not touch Odoo.

```ini
[options]
rec_encryption_key_provider = file
rec_encryption_key_path = /run/secrets/odoo-encryption/keyring
```

```bash
export REC_ENCRYPTION_KEY_PROVIDER=file
export REC_ENCRYPTION_KEY_PATH=/run/secrets/odoo-encryption/keyring
```

### File Format

Any of these are accepted. Versions follow the same rules as everywhere else:
integers, highest is current, and a bare key means version `0`.

One line, like the config string:

```
0:<key0>,1:<key1>
```

One entry per line, with comments — usually easier to review in a diff:

```
# retired 2026-08-01
0:<key0>
# current
1:<key1>
```

JSON, for tooling that renders it:

```json
{"0": "<key0>", "1": "<key1>"}
```

### Rotation

The file is an externally managed source, so it is polled exactly like GCP:
replace it with one that has an extra version, and the cron discovers the
change, signals every worker, and re-encrypts on the following run. See
[Hands-off Rotation with GCP](#hands-off-rotation-with-gcp) — the mechanism is
identical, only the source differs.

> **Kubernetes**: mount the **directory**, not the file. A volume mounted with
> `subPath` is not refreshed by kubelet when the secret changes, so the new
> keyring would never appear.

Protect the file with filesystem permissions: it holds key material in
plaintext, exactly like the config provider.

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
decrypts with version `1`. Restart **every** worker — see
[When Keys Are Re-read](#when-keys-are-re-read).

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

If the original key was unversioned, give it version `0` — that is the version
its existing blobs already resolve to.

#### 3. Restart Odoo

- **New writes** are encrypted with key version `1`.
- **Old reads** transparently decrypt using key version `0`.
- No downtime, no data loss.
- Restart **every** worker — see [When Keys Are Re-read](#when-keys-are-re-read).

#### 4. Re-encrypt Existing Data

Nothing to do — this happens automatically during the restart above, and there
is no table list to maintain because encryption columns are discovered by field
type. See [Automatic Re-encryption](#automatic-re-encryption).

If you have disabled automatic re-encryption, trigger it yourself:

```python
env['base']._re_encrypt_now()
env.cr.commit()
```

Or, from a bare cursor:

```python
from odoo.addons.hibou_field_encryption.models.fields import re_encrypt_all

results = re_encrypt_all(env.cr, registry=env.registry)
env.cr.commit()

for (table, column), updated in results.items():
    print(f"{table}.{column}: {updated} rows")
```

To see which columns would be processed:

```python
from odoo.addons.hibou_field_encryption.models.fields import find_encryption_columns

find_encryption_columns(env.cr, registry=env.registry)
# [('enc_test_sugar', 'rec_encrypted'), ('res_partner', 'my_blob'), ...]
```

A single table can still be targeted, and returns the number of rows that were
actually updated:

```python
from odoo.addons.hibou_field_encryption.models.fields import re_encrypt_table

updated = re_encrypt_table(env.cr, 'eyrie_datasource')
print(f"Re-encrypted {updated} rows in eyrie_datasource")
```

For a custom encryption field name, and a larger batch size:

```python
re_encrypt_table(env.cr, 'my_table', encryption_field='my_custom_enc', batch_size=5000)
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

Keep the versioned form: the blobs now carry version `1`, while a bare
`rec_encryption_key` would be loaded as version `0`.

> **Warning**: If any row is still encrypted with the removed version, that data
> will be **permanently unreadable**. Verify with
> `env['ir.config_parameter'].get_param('encryption.migrated_key_version')`
> before removing anything — and remember that database *backups* restored later
> still contain the old version.

#### 6. Subsequent Rotations

```bash
# Second rotation
export REC_ENCRYPTION_KEY="1:<key1>,2:<key2>"

# Third rotation
export REC_ENCRYPTION_KEY="2:<key2>,3:<key3>"
```

---

## Automatic Re-encryption

**Add a key version, restart, done.** Rotation is automatic and requires no
other action: if the keyring holds more than one key version and the database
has not been stamped with the current version, all encrypted columns are
rewritten to the current key during startup.

Behaviour:

- Runs from `_register_hook()` at registry load, after all models are set up
  and before the registry serves requests. It is hooked on a single concrete
  model (`ir.model.fields`) rather than on `base`, because `_register_hook()`
  is called once *per model* — hooking it on `base` would reload the keyring
  hundreds of times per boot, and with the GCP provider that means hundreds of
  Secret Manager calls.
- No-ops unless the keyring has more than one version **and**
  `encryption.migrated_key_version` is behind the current version. On an
  already-rotated database the cost is two small queries per boot.
- Also runs on module install/upgrade, since those reload the registry.
- Takes a Postgres transaction-level advisory lock, so with multiple workers
  only one performs the rewrite; the others log and continue.
- The pass is **blocking**. It logs at `WARNING` before starting:

  ```
  Encryption key rotation to version 1 detected. Re-encrypting all encrypted
  fields now; this instance will NOT serve requests until it finishes.
  ```

  and again on completion, with the elapsed time.
- Commits when finished, then stamps `encryption.migrated_key_version`.
- On failure it logs the traceback and lets the boot continue — the old key is
  still in the keyring, so data stays readable and the hourly cron retries.

### When Keys Are Re-read

The keyring is cached **per process**. It is re-read at exactly one moment:
**registry load** — process start, module install/upgrade, or a registry
signal. That moment is deliberate, because it is the only one that happens in
*every* process, so the whole fleet converges on the same keyring.

With the **config** provider the cron deliberately does **not** re-read the key
source. It is a single process, and a key version only it knew about would be a
split brain: it would rotate every row to version `2` while every HTTP worker
carried on writing version `1`, and the rotation would already have been
stamped. A config value cannot change under a running process anyway, so after
editing it, restart **all** workers.

With **GCP** the key set *can* change while Odoo runs, so the cron polls for it
— but only in a way that keeps the fleet together. See
[Hands-off Rotation with GCP](#hands-off-rotation-with-gcp).

#### Refreshing Without a Full Restart

Because the refresh is tied to registry load, you can force it fleet-wide by
signalling the registry — the same mechanism a module install uses. Every other
worker notices on its next request and rebuilds:

```python
env.registry.signal_changes()
env.cr.commit()
```

That is a real registry rebuild, so it costs roughly what a module upgrade
costs. It is useful for the GCP provider, where the key set can change without
anything on the server changing.

#### Before Deleting a Retired Key

The stamp is only written once `pending_re_encrypt_count()` reports zero across
every column, so a straggler written *during* a pass blocks it. A row written
*after* a completed pass is still readable — the retired key is in the keyring —
but it will not be picked up until the next rotation. That matters at exactly
one moment: before deleting a retired key. Restart everything, then confirm:

```python
env['ir.config_parameter'].get_param('encryption.migrated_key_version')
env['base']._encryption_rotation_pending()   # None when nothing is outstanding
```

### The Cron

An hourly `ir.cron` (`_cron_re_encrypt_fields`) has always been the module's
rotation mechanism; it is now a **catch-up** for the cases the startup pass
cannot cover:

- The startup pass failed part-way (bad row, disk full, timeout).
- A database was restored from a backup that predates the rotation, without a
  restart.
- Another process held the advisory lock and this one skipped.

It honours the same disable flag, so there is no configuration in which both run
unexpectedly. Unlike the startup pass, it runs **incrementally**, because it
shares the database with live traffic:

| | Startup pass | Cron pass |
|---|---|---|
| Transaction | one, for the whole rotation | one per batch |
| Contended rows | waits for them | `SKIP LOCKED`, retried next run |
| Duration | until finished | `REENCRYPT_CRON_TIME_BUDGET` (300s), then resumes |
| Advisory lock | held throughout | re-taken each batch |
| Interrupted | loses the pass, retries | keeps completed batches |

Why the difference matters:

- **Row locks are held until commit.** A single-transaction pass over the whole
  database ends up holding a write lock on *every* encrypted row. Reads are
  unaffected (MVCC), but any user write to those rows blocks until the pass
  finishes. At startup that is harmless because nothing is serving yet; during
  the day it is not.
- **Odoo cursors run at `REPEATABLE READ`.** If another transaction updates a
  row that a long-running pass then tries to update, PostgreSQL raises *could
  not serialize access due to concurrent update* and the **entire** pass rolls
  back. Committing per batch keeps that blast radius to one batch, and
  `SKIP LOCKED` mostly avoids the collision in the first place.
- **Progress is durable.** Because every blob records its own key version,
  committed batches are simply not selected again. An interrupted cron pass
  loses at most one batch.
- **A cron worker is a scarce resource.** `--max-cron-threads` defaults to 2, so
  a multi-hour job would starve other scheduled work. The time budget releases
  the worker and resumes on the next run.

The rotation is only stamped once `pending_re_encrypt_count()` reports zero rows
left across every column, so a budget-limited run correctly leaves the rotation
open and the old key required.

### Cost and Throughput

Re-encryption is CPU-bound on Fernet, roughly 10–100k blobs/second/core, so the
rewrite itself is rarely the constraint. The costs to plan for are:

- **Write amplification.** Every row is rewritten, so the table's heap roughly
  doubles until autovacuum reclaims the dead tuples, and each rewrite is
  WAL-logged (and shipped to replicas). This is inherent to rotating keys, not
  to this implementation.
- **Scan cost per run.** The pending filter reads the version header in SQL, so
  it never decrypts unnecessarily, but it is still a sequential scan per column
  per run. For an unusually large encrypted table, a partial index makes
  repeated passes cheap:

  ```sql
  CREATE INDEX CONCURRENTLY my_table_reencrypt_pending_idx
      ON my_table (id)
   WHERE rec_encrypted IS NOT NULL;
  ```

### Which Should You Rely On?

- **Startup pass (default).** Fastest wall-clock rotation, no contention, at the
  cost of a delayed boot. Best when the encrypted tables are small — which is
  the usual case, since they hold secrets rather than transactional data.
- **Cron only.** Set `rec_encryption_disable_auto_reencrypt` for the restart
  that introduces the new key, then clear it once the instance is up: the cron
  will grind through the rotation in 300-second slices without a visible outage.
  Rotation takes longer in wall-clock terms and the old key must stay configured
  until `encryption.migrated_key_version` catches up.
- **Manual.** Disable both and call `env['base']._re_encrypt_now()` in a
  maintenance window for full control.

### Disabling It

If the pass is too slow for your startup budget, or a rotation went badly and
you want to take back control:

```ini
[options]
rec_encryption_disable_auto_reencrypt = True
```

```bash
export REC_ENCRYPTION_DISABLE_AUTO_REENCRYPT=1
```

This disables **both** the startup pass and the cron. Nothing breaks: the
keyring still contains every key, so old blobs stay readable and new writes use
the current key. Only the rewrite is deferred, and the old key must stay
configured until you perform it.

Rotate manually when it suits you:

```bash
odoo shell -d mydb
```

```python
env['base']._re_encrypt_now()
env.cr.commit()
```

`_re_encrypt_now()` ignores the disable flag, logs per-column row counts, and
stamps `encryption.migrated_key_version` on success — so a later restart with
the flag removed will correctly see nothing to do.

To check what is outstanding at any time:

```python
env['base']._encryption_rotation_pending()   # current key version, or None
env['base']._encryption_migrated_version()   # last version fully rotated to
```

---

## Can PostgreSQL Do the Re-encryption?

Short answer: it can, but it is rarely worth it.

**What PostgreSQL cannot do out of the box.** Fernet is not a Postgres format.
A Fernet token is `base64url(0x80 || timestamp(8B) || IV(16B) ||
AES-128-CBC ciphertext || HMAC-SHA256(32B))`, and the 32-byte Fernet key is
split into a 16-byte signing key and a 16-byte encryption key. `pgcrypto`
exposes all of those primitives (`encrypt_iv`/`decrypt_iv` with
`aes-cbc/pad:pkcs`, `hmac`, `gen_random_bytes`, `encode`/`decode` for base64),
so a `plpgsql` function *can* reproduce Fernet exactly and a rotation becomes a
single set-based statement per table:

```sql
UPDATE res_partner
   SET rec_encrypted = fernet_rewrap(rec_encrypted, :old_key, :new_key, 1)
 WHERE rec_encrypted IS NOT NULL
   AND get_byte(rec_encrypted, 0) = 1
   AND (get_byte(rec_encrypted, 1) << 8) + get_byte(rec_encrypted, 2) < 1;
```

**Why we do not do this.**

- The key material has to be handed to the database. It shows up in
  `pg_stat_activity`, in `log_statement`/`log_min_duration_statement` output, in
  `EXPLAIN` plans, and in any query capture. That defeats the main point of
  application-side encryption: the DBA/backup holder never sees the key.
- `pgcrypto` must be installed and its base64 output is line-wrapped, which has
  to be stripped; the Fernet URL-safe alphabet also needs translating. It is
  fiddly cryptographic code living outside the test suite that covers the Python
  path.
- The Python path is not the bottleneck. With batched keyset pagination and one
  array-based `UPDATE` per batch, rewrapping is dominated by Fernet itself
  (roughly 10–100k blobs/second per core), and these tables hold secrets, not
  millions of rows.

**Where PostgreSQL does help.**

- Discovery, via `information_schema` / `ir_model_fields` (used as a fallback by
  `find_encryption_columns()` when no registry is available).
- Cheap filtering: the version header is the first three bytes, so
  `get_byte(col, 0) = 1` and the uint16 at offsets 1–2 identify rows that still
  need work without decrypting anything.
- Advisory locks (`pg_try_advisory_xact_lock`), used to serialize the boot-time
  pass across workers.
- Set-based writes: `UPDATE ... FROM unnest(%s::bigint[], %s::bytea[])`, which
  is how batches are applied.

If you truly need in-database rotation (e.g. a multi-terabyte table with a
maintenance window), the honest alternative is to move the whole scheme to
`pgcrypto` or to PostgreSQL TDE / filesystem-level encryption rather than
splitting the format between two implementations.

---

## Configuration Reference

| Config Key | Environment Variable | Default | Description |
|---|---|---|---|
| `rec_encryption_key_provider` | `REC_ENCRYPTION_KEY_PROVIDER` | `config` | Key provider: `config` or `gcp_secret_manager` |
| `rec_encryption_key` | `REC_ENCRYPTION_KEY` | *(required for config provider)* | Single Fernet key or versioned keyring |
| `rec_encryption_key_path` | `REC_ENCRYPTION_KEY_PATH` | *(required for file provider)* | Path to a file holding the keyring |
| `rec_encryption_disable_auto_reencrypt` | `REC_ENCRYPTION_DISABLE_AUTO_REENCRYPT` | `False` | Opt out of automatic re-encryption at startup and in the cron |
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

You do not have to. `find_encryption_columns()` does it by field type, and both
`re_encrypt_all()` and the cron use it:

```python
from odoo.addons.hibou_field_encryption.models.fields import find_encryption_columns

find_encryption_columns(env.cr, registry=env.registry)
```

It unions two sources, then verifies the result:

1. **The registry** (authoritative): every field whose `type == 'encryption'`,
   mapped to its model's `_table`. Abstract models are skipped, and custom
   `_table` names are handled correctly.
2. **The database catalog** (supplement): `bytea` columns named `rec_encrypted`,
   plus any `ir_model_fields` row with `ttype = 'encryption'`. This catches
   tables left behind by uninstalled or not-yet-loaded modules — rows that
   would otherwise be stranded on a retired key.
3. **Verification**: every candidate is checked against
   `information_schema.columns` and dropped unless it exists as a `bytea`
   column on a base table. A field can be declared in Python before its table
   exists (mid-install, or a module whose update has not run yet), and passing
   that to `re_encrypt_table()` would raise on a missing relation and abort the
   entire rotation. So every returned pair is safe to query.

When called without a registry (migration scripts, plain cursor) it falls back
to the catalog only, so it is safe to use from `pre-`/`post-migration` scripts:

```python
from odoo.addons.hibou_field_encryption.models.fields import re_encrypt_all

def migrate(cr, version):
    re_encrypt_all(cr)
```

The equivalent raw queries, if you want to check by hand:

```sql
SELECT table_name, column_name
FROM information_schema.columns
WHERE table_schema = current_schema()
  AND udt_name = 'bytea'
  AND column_name = 'rec_encrypted'
ORDER BY table_name;

SELECT m.model, f.name
FROM ir_model_fields f
JOIN ir_model m ON m.id = f.model_id
WHERE f.ttype = 'encryption';
```

And, to count rows still on an old key version without decrypting anything:

```sql
SELECT count(*)
FROM res_partner
WHERE rec_encrypted IS NOT NULL
  AND (get_byte(rec_encrypted, 0) <> 1
       OR (get_byte(rec_encrypted, 1) << 8) + get_byte(rec_encrypted, 2) < 1);
```

---

## Switching Between Providers

Every blob stores the **key version number** it was encrypted with, and the
provider has to supply a key under that exact number. The two providers differ
in who chooses those numbers:

- **config** — you choose them (`0:<k0>,1:<k1>`), and a bare key means `0`.
- **gcp_secret_manager** — GCP chooses them. Secret versions start at `1` and
  increment; you cannot create a version `0`.

So the two directions are not symmetrical.

> **Warning**: a wrong version-to-key mapping fails **silently**. Reads return
> empty values and an ERROR is logged, rather than raising. Always take the
> inventory below before and after switching.

### Inventory First

```python
from odoo.addons.hibou_field_encryption.models.fields import (
    encryption_version_histogram,
)

encryption_version_histogram(env.cr, registry=env.registry)
# {('res_partner', 'rec_encrypted'): {0: 412}}
```

The version numbers this reports are exactly the ones the new provider must be
able to supply. It reads the header in SQL, so it needs no keyring and works
even when the current configuration cannot load one.

### Config → GCP

Data sitting on version `0` can never be read by a GCP keyring. Move it onto
version `1` **before** switching, while the config provider can still read it.

1. **Consolidate onto version 1.** Give the current key the number `0` and add
   version `1`:

   ```bash
   export REC_ENCRYPTION_KEY="0:<current_key>,1:<key_for_version_1>"
   ```

   `<key_for_version_1>` may be a brand new key (a real rotation) or the same
   key again (a pure header renumbering). Both are valid; reuse the same key if
   you only want to migrate provider, not rotate.

2. **Restart every worker** and let the rotation finish, then confirm only
   version `1` remains:

   ```python
   encryption_version_histogram(env.cr, registry=env.registry)
   # {('res_partner', 'rec_encrypted'): {1: 412}}
   ```

3. **Drop the retired key** and restart: `REC_ENCRYPTION_KEY="1:<key1>"`.
   Verify an encrypted field still reads correctly.

4. **Create the secret fresh** with that key, and confirm it really is
   version `1`:

   ```bash
   echo -n "<key1>" \
       | gcloud secrets create odoo-encryption-key \
           --project=my-gcp-project \
           --replication-policy=automatic \
           --data-file=-

   gcloud secrets versions list odoo-encryption-key --project=my-gcp-project
   ```

5. **Switch the provider** and restart every worker:

   ```bash
   export REC_ENCRYPTION_KEY_PROVIDER=gcp_secret_manager
   export REC_ENCRYPTION_GCP_PROJECT=my-gcp-project
   export REC_ENCRYPTION_GCP_SECRET=odoo-encryption-key
   ```

6. **Verify**, then remove `REC_ENCRYPTION_KEY`. Keep the key material in your
   own backup regardless — it is the rollback path.

If your data is on some other number (say version `5`), a fresh GCP secret
cannot reproduce it without creating five versions. Consolidate onto a single
version first; that is what step 1 is for.

Do **not** push a multi-key keyring into GCP by adding several versions and
hoping the numbers line up. If `0:<kA>,1:<kB>` becomes GCP versions `1:<kA>`
and `2:<kB>`, then blobs tagged `1` are decrypted with `kA` instead of `kB` —
wrong key, silent empty reads.

### GCP → Config

Straightforward, because you can reproduce GCP's numbering exactly. No
re-encryption is needed.

1. **List the enabled versions** and read each payload:

   ```bash
   gcloud secrets versions list odoo-encryption-key --project=my-gcp-project
   gcloud secrets versions access 1 --secret=odoo-encryption-key --project=my-gcp-project
   ```

2. **Write them into the config string under the same numbers**:

   ```bash
   export REC_ENCRYPTION_KEY="1:<v1_key>,2:<v2_key>"
   ```

   Use the versioned form even for a single key: a bare key would be loaded as
   version `0` and would not match anything GCP wrote.

3. **Switch the provider back** (unset `REC_ENCRYPTION_KEY_PROVIDER`, or set it
   to `config`) and restart every worker.

4. **Verify** that every version in the inventory is present in your keyring,
   then retire the GCP secret.

### Rolling Back

Until you have destroyed key material, either direction is reversible: the
blobs are unchanged and only the source of the keys differs. Keep the old
provider configured and readable until the inventory confirms the new one
covers every version in use.

---

## Hands-off Rotation with GCP

With `gcp_secret_manager`, rotating a key is: **add a secret version, wait,
disable the old one.** No config edit, no restart.

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" \
    | gcloud secrets versions add odoo-encryption-key \
        --project=my-gcp-project --data-file=-
```

What happens next, one cron run at a time:

1. **Discovery.** The cron re-reads Secret Manager, sees the version set has
   changed, and signals every worker to rebuild its registry — which is what
   makes them re-read the keys. It then stops without re-encrypting, and logs:

   ```
   Encryption key versions changed from [1] to [1, 2]. Every worker has been
   signalled to reload; re-encryption starts on the next run.
   ```

2. **Convergence.** Each worker rebuilds on its next request and starts writing
   with version `2`.

3. **Rotation.** The following cron run re-encrypts existing rows to version
   `2`, incrementally, and stamps `encryption.migrated_key_version` once no row
   is left behind.

Rotation is deliberately deferred to a later run than discovery. Rotating in
the same pass would rewrite rows to a version the other workers were not yet
writing, which is the split brain the design avoids.

### When Is It Safe to Disable the Old Version?

When nothing is outstanding and no blob still carries the old number:

```python
env['base']._encryption_rotation_pending()   # None
encryption_version_histogram(env.cr, registry=env.registry)
# {('res_partner', 'rec_encrypted'): {2: 412}}   # only the new version
```

The histogram is the authoritative check — it reads what is actually stored,
rather than what the stamp claims. Only then:

```bash
gcloud secrets versions disable 1 --secret=odoo-encryption-key \
    --project=my-gcp-project
```

Disabling propagates the same way: the cron notices the version set changed and
signals the fleet again.

### Failure Behaviour

- **Secret Manager unreachable**: the poll logs and keeps the keyring the
  process already has. Nothing breaks; it retries next run.
- **Signalling unavailable**: the poll rolls its own keyring back, so it cannot
  become the only process on the new key. It retries next run.
- **Disabled too early**: rows on the removed version log
  `encrypted with revoked key version N` and read as empty until you re-enable
  it. Re-enabling restores them — the ciphertext is untouched.

Set `rec_encryption_disable_auto_reencrypt` to turn all of this off, including
the polling.

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

Recovery requires the original key. Add it back to the keyring — re-enable the
GCP version, or put it back in the versioned config string under the version the
blobs claim (`0:<original_key>,1:<current_key>`) — and restart. Automatic
re-encryption then completes the rotation before you remove it again.

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
