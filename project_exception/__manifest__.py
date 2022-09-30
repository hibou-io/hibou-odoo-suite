# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': "Project Exception Rule",
    'version': '15.0.1.0.0',
    'author': "Hibou Corp.",
    'license': 'OPL-1',
    'category': 'Generic Modules',
    'summary': """
        Module for Project Exception Rule""",
    'description': """
        The ability to run and trigger exceptions to block the moving of a task based on rules
    """,    
    'website': "http://www.hibou.io/",
    'depends': [
        'base_exception_user',
        'project'
    ],    
    'data': [
        'security/ir.model.access.csv',
        'views/project_views.xml',
        'wizard/project_exception_confirm_views.xml',
    ],    
    'demo': [
        'demo/project_exception_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
}
