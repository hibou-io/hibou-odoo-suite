{
    'name': 'Web Date Warning',
    'version': '12.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'website': 'https://hibou.io/',
    'license': 'AGPL-3',
    'category': 'Tools',
    'complexity': 'expert',
    'description': """
#Web Date Warning

Provides warnings for date field entries that fall outside of a user-specified range, with the goal of reducing data entry errors.

* For any date or date/time picker, set the threshold that should trigger the warning
* Allows you to set a threshold for past, future or both
* In addition to displaying warning text, will also display how many days in the past or future the selected date is

On a record with the date or date/time picket you wish to add the warning to, edit the form view and create an inherited view. Target the field name and include the following details:


`widget="date-warn"` if the field is a date picker

`widget="datetime-warn"` if the field is a date/time picker

`options="{'warn_future': 90}"` to set a threshold for future dates where 90 is the number of days

And/or `options="{'warn_past': 30}"` to set a threshold for past dates where 30 is the number of days


**Example:**

`<field name="date_invoice" widget="date-warn" options="{'warn_future': 90, 'warn_past': 30}"/>`
    """,
    'depends': [
        'web',
    ],
    'data': [
        'views/web_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'category': 'Hidden',
}
