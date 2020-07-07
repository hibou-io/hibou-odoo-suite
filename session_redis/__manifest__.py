{
    "name": "Redis Sessions",
    "version": "13.0.1.0.0",
    "depends": ["base"],
    "author": "Hibou Corp.",
    "license": "AGPL-3",
    "description": """Use Redis for Session storage instead of File system

To use, you must load `session_redis` as a server wide module.
Example Configuration file overrides un-needed ones will be commented and show the default or example.

server_wide_modules = web,session_redis
session_redis = True
;session_redis_host = localhost
;session_redis_port = 6379
;session_redis_dbindex = 1
;session_redis_pass = x
;session_redis_expire = 604800
;session_redis_prefix = test

    """,
    "summary": "",
    "website": "",
    "category": 'Tools',
    "auto_install": False,
    "installable": True,
    "application": False,
    "external_dependencies": {
        'python': ['redis'],
    },
}
