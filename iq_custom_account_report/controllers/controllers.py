# -*- coding: utf-8 -*-
# from odoo import http


# class IqCustomAccountReport(http.Controller):
#     @http.route('/iq_custom_account_report/iq_custom_account_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/iq_custom_account_report/iq_custom_account_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('iq_custom_account_report.listing', {
#             'root': '/iq_custom_account_report/iq_custom_account_report',
#             'objects': http.request.env['iq_custom_account_report.iq_custom_account_report'].search([]),
#         })

#     @http.route('/iq_custom_account_report/iq_custom_account_report/objects/<model("iq_custom_account_report.iq_custom_account_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('iq_custom_account_report.object', {
#             'object': obj
#         })
