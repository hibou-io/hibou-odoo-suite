# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': "Timesheet Exception Rule",
    'version': '15.0.1.0.0',
    'author': "Hibou Corp.",
    'license': 'OPL-1',
    'category': 'Generic Modules',
    'summary': """
        Module for Timesheet Exception Rule""",
    'description': """
        The ability to run and trigger exceptions to block the moving of a timesheet based on rules
    """,    
    'website': "http://www.hibou.io/",
    'depends': [
        'base_exception_user',
        'timesheet_grid',
        'sale_timesheet'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/timesheet_views.xml',
        'wizard/timesheet_exception_confirm_views.xml',
    ],
    'demo': [
        'demo/timesheet_exception_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
}
