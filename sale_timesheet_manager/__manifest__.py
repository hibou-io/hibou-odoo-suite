# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Hibou Project Time Manager',
    'version': '13.0.1.3.0',
    'category': 'Warehouse',
    'author': 'Hibou Corp.',
    'license': 'OPL-1',
    'website': 'https://hibou.io/',
    'depends': [
        'sale_timesheet',
        'website',
    ],
    'data': [
        'security/ir.model.access.csv',
        # 'views/project_views.xml',
        'views/time_manager_templates.xml',
        'views/web_assets.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
 }
