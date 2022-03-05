# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import Warning


class ResPartnerInherit(models.Model):
	_inherit = 'res.partner'
	# Customer  Info
	client_address_1 = fields.Char("عنوان الزبون",)
	client_phone_1 = fields.Char("هاتف الزبون", )
	driver_name_1 = fields.Char("اسم السائق",)
	no_car_1 = fields.Char("رقم المركبة", )
	order_no_1 = fields.Char("رقم الطلب", )
	inv_no_1 = fields.Char("رقم الفاتورة",)


