# -*- coding: utf-8 -*-
#
#
#    Author: Jared Kipe
#    Copyright 2017 Hibou Corp.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

{
    'name': 'US ZIP Code to City/State',
    'summary': 'Determines the City and State from a provided ZIP code.',
    'version': '10.0.1.0.0',
    'author': "Hibou Corp.",
    'category': 'Localization',
    'license': 'AGPL-3',
    'complexity': 'easy',
    'images': [],
    'website': "https://hibou.io",
    'description': """
US ZIP Code to City/State
=========================

Determines the City and State from a provided ZIP code. Requires the `uszipcode` python package.

Does not require `base_geolocalize`, but will fill the related fields if possible.


Contributors
------------

* Jared Kipe <jared@hibou.io>

""",
    'depends': [
        'base',
    ],
    'external_dependencies': {
        'python': ['uszipcode']
    },
    'demo': [],
    'data': [
    ],
    'auto_install': False,
    'installable': True,
}
