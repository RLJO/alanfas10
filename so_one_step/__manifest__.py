# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'SO One step',
    'version' : '1.0',
    'author':'Abdulrhman',
    'category': 'Sales',
    'maintainer': 'Abdulrhman',
    'summary': """You can directly create invoice and set done to delivery order by single click.""",
    'description': """
        You can directly create invoice and set done to delivery order by single click
    """,
    'website': '',
    'license': 'LGPL-3',
    'support':'',
    'depends' : ['sale_management','stock','sale'],
    'data': [
        # 'views/stock_warehouse.xml',
        'views/sale_order.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    # 'images': ['static/description/icon.png'],

}
