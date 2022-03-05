{
    'name': "Sales Enhancement",
    'author': 'Elsadany',
    'category': 'Sale',
    'summary': """This module do some modifications on default sales""",
    'website': '',
    'license': 'AGPL-3',
    'description': """
    This module do some modifications on default sales
""",
    'version': '1.0',
    'depends': ['base','sale','account','stock','stock_landed_costs'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/partner_view_changes.xml',
        'views/sale_order_changes.xml',
        'views/account_move_changes.xml',
        'views/stock_picking.xml',
        'views/picking_report.xml',
        'views/sale_report.xml',
        'views/invoice_report.xml',
        'views/landed_cost.xml',

    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
