{
    "name": "Attachment MinIO",
    "version": "13.0.1.0.0",
    "depends": [
        "base_attachment_object_storage",
    ],
    "author": "Hibou Corp.",
    "license": "AGPL-3",
    "description": """
# Use MinIO (or Amazon S3) for Attachment/filestore

MinIO provides S3 API compatible storage to scale out without a shared filesystem like NFS.

This module will store the bucket used in the attachment database object, thus allowing 
you to retain read-only access to the filestore by simply overriding the bucket.

## Setup details

Before installing this app, you should add several System Parameters (the most important of
which is `ir_attachment.location`), OR set them through the config file as described later.

**The in database System Parameters will act as overrides to the Config File versions.**

| Key                               | Example Value | Default Value |
|-----------------------------------|---------------|---------------|
| ir_attachment.location            | s3            |               |
| ir_attachment.location.host       | minio:9000    |               |
| ir_attachment.location.bucket     | odoo          |               |
| ir_attachment.location.region     | us-west-1     | us-west-1     |
| ir_attachment.location.access_key | minio         |               |
| ir_attachment.location.secret_key | minio_secret  |               |
| ir_attachment.location.secure     | 1             |               |

**Config File:**

```
attachment_minio_host = minio:9000
attachment_minio_region = us-west-1
attachment_minio_access_key = minio
attachment_minio_secret_key = minio_secret
attachment_minio_bucket = odoo
attachment_minio_secure = False
```

In general, they should all be specified other than "region" (if you are not using AWS S3) 
and "secure" which should be set if the "host" needs to be accessed over SSL/TLS.

Install `attachment_minio` and during the installation `base_attachment_object_storage` should move 
your existing filestore attachment files into the database or object storage.

For example, you can run a shell command like the following to set the parameter:

```
env['ir.config_parameter'].set_param('ir_attachment.location', 's3')
# If already installed...
# env['ir.attachment'].force_storage()
env.cr.commit()
```

If `attachment_minio` is not already installed, you can then install it and the migration 
should be noted in the logs.  **Ensure that the timeouts are long enough that the migration can finish.**

    """,
    "summary": "",
    "website": "",
    "category": 'Tools',
    "auto_install": False,
    "installable": True,
    "application": False,
    "external_dependencies": {
        "python": [
            "minio",
        ],
    },
}
