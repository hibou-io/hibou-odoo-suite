# -*- coding: utf-8 -*-

{
    'name': "Project Exception Rule",

    'summary': """
        Module for Project Exception Rule""",

    'description': """
        The ability to run and trigger exceptions to block the moving of a task based on rules
    """,

    'author': "Hibou Corp.",
    'website': "http://www.hibou.io/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Generic Modules',
    'version': '15.0.1.0.0',
    'license': 'OPL-1',

    # any module necessary for this one to work correctly
    'depends': ['base_exception_user', 'project'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/project_views.xml',
        'wizard/project_exception_confirm_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/project_exception_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
}
