# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'PO One step',
    'version' : '1.0',
    'author':'Abdulrhman',
    'category': 'Purchase',
    'maintainer': 'Abdulrhman',
    'summary': """You can directly create invoice and set done to delivery order by single click.""",
    'description': """
        You can directly create invoice and set done to delivery order by single click
    """,
    'license': 'LGPL-3',
    'depends' : ['purchase'],
    'data': [
        'views/purchase_order.xml'
    ],
    'installable': True,

}
