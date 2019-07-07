{
    "name": "Attachment MinIO",
    "version": "11.0.1.0.0",
    "depends": [
        "base_attachment_object_storage",
    ],
    "author": "Hibou Corp.",
    "license": "AGPL-3",
    "description": """
#################################################
Use MinIO (or Amazon S3) for Attachment/filestore
#################################################

MinIO provides S3 API compatible storage to scale out without a shared filesystem like NFS.


Setup details
#############

Before installing this app, you should add several System Parameters.

Key : Example Value : Default Value

ir_attachment.location : s3 : _

ir_attachment.location.host : minio.yourdomain.com : _

ir_attachment.location.bucket : odoo-prod : _

ir_attachment.location.region : us-west-1 : us-west-1

ir_attachment.location.access_key : odoo : _

ir_attachment.location.secret_key : 123456 : _

ir_attachment.location.secure : 1 : _


In general, they should all be specified other than "region" (if you are not using AWS S3) 
and "secure" which should be set if the "host" needs to be accessed over SSL/TLS.

Install `attachment_minio` and during the installation `base_attachment_object_storage` should move 
your existing filestore attachment files into the database or object storage.
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
