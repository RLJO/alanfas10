from odoo import models, tools, api, fields



class f_falak_prodmoves_details(models.Model):
    _name = 'f.account.details.moves'
    _description = "Accounting Details  Report"
    _auto = False
    _order='date asc , id asc'
    
    
    customer_pay = fields.Float(string='مقبوضات', digits=0, readonly=True)
    vendor_pay= fields.Float(string='مدفوعات', digits=0, readonly=True)
    inv_bill_amount= fields.Float(string='مبلغ القائمة', digits=0, readonly=True)
    currency_id = fields.Many2one('res.currency', string='العملة', readonly=True)
    type=fields.Char('نوع الحركة', readonly=True)
    ref=fields.Char('رقم الحركة', readonly=True)
    partner_id = fields.Many2one('res.partner', string='جهة الحركة', readonly=True)
    note=fields.Char('التفاصيل', readonly=True)
    date = fields.Date('تاريخ الحركة', readonly=True)
    
    