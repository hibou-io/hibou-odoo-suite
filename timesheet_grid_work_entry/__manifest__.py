# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Timesheet Grid Work Entry',
    'description': 'bridge',
    'version': '15.0.1.0.1',
    'website': 'https://hibou.io/',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'OPL-1',
    'category': 'Human Resources',
    'depends': [
        'hr_timesheet_work_entry',
        'timesheet_grid',
    ],
    'data': [
        'views/timesheet_views.xml',
        'wizard/project_task_create_timesheet_views.xml',
        'wizard/timesheet_merge_wizard_views.xml',
    ],
    'demo': [
    ],
    'assets': {
        'web.assets_backend': [
#            'timesheet_grid_work_entry/static/src/js/timesheet_grid/timesheet_timer_grid_renderer.js',
#            'timesheet_grid_work_entry/static/src/js/timesheet_grid/timesheet_timer_grid_view.js',
#            'timesheet_grid_work_entry/static/src/js/timesheet_grid/timer_m2o.js',
#            'timesheet_grid_work_entry/static/src/js/timesheet_grid/timer_header_component.js',
        ],
        'web.assets_qweb': [
 #           'timesheet_grid_work_entry/static/src/xml/**/*',
        ],
    },
    'installable': True,
    'auto_install': True,
    'application': False,
}
