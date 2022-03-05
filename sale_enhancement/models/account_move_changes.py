# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountMoveInherit12(models.Model):
    _inherit = 'account.move'

    # Customer Info in partner
    client_address_1 = fields.Char("عنوان الزبون", related="partner_id.client_address_1",readonly=False)
    client_phone_1 = fields.Char("هاتف الزبون", related="partner_id.client_phone_1",readonly=False)
    driver_name_1 = fields.Char("اسم السائق", related="partner_id.driver_name_1",readonly=False)
    no_car_1 = fields.Char("رقم المركبة", related="partner_id.no_car_1",readonly=False)
    order_no_1 = fields.Char("رقم الطلب", related="partner_id.order_no_1",readonly=False)
    inv_no_1 = fields.Char("رقم الفاتورة", related="partner_id.inv_no_1",readonly=False)

    payment_state = fields.Selection(selection=[
        ('not_paid', 'Not Paid'),
        ('in_payment', 'تم الدفــع'),
        ('paid', 'Paid'),
        ('partial', 'دفع جزئـي'),
        ('reversed', 'Reversed'),
        ('invoicing_legacy', 'Invoicing App Legacy')],
        string="Payment Status", store=True, readonly=True, copy=False, tracking=True,
        compute='_compute_amount')
