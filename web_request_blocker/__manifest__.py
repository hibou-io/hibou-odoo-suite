{
    'name': 'Hibou Web Request Blocker',
    'category': 'System',
    'version': '14.0.1.0.0',
    'description': """
Hibou Web Request Blocker
=========================

This module blocks undesirable web requests through user agent matching.
Default pattern by the ai.robots.txt project https://github.com/ai-robots-txt/

Configuration key (by decreasing priority: ir.config_parameter / environment / odoo.conf)
'web_request_blocker.user_agent_pattern'

Force conf/env key, ignoring ir.config_paraneter:
'web_request_blocker.force_user_agent_pattern'
        """,
    'depends': [
        'base',
    ],
    'data': [
        'data/ir_config_parameter.xml',
    ],
    'auto_install': True,
    'license': 'AGPL-3',
}
