# -*- coding: utf-8 -*-
# © 2017 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{'name': 'Reorder Rules per Warehouse',
 'version': '10.0.1.0.0',
 'category': 'Warehouse',
 'depends': ['stock',
             ],
 'description': """
Patches `procurement.orderpoint.compute` wizard to allow running on demand per-warehouse.

 """,
 'author': "Hibou Corp.",
 'license': 'AGPL-3',
 'website': 'https://hibou.io/',
 'data': [
  'wizard/procurement_order_compute_views.xml',
 ],
 'installable': True,
 'application': False,
 }
