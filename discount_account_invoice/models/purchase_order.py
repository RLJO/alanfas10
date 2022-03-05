# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PurchaseOrderDiscount(models.Model):
    _inherit = "purchase.order"

    @api.depends('order_line.price_total', 'order_line.discount', 'order_line.product_uom_qty')
    def _amount_discount(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            discount = 0.0
            for line in order.order_line:
                discount += line.discount if line.discount_type == 'fixed' else line.product_qty * line.price_unit * line.discount / 100.0
            #order.update({
                #'total_discount': discount,
            #})
            order.total_discount = discount + order.total_global_discount


    @api.depends('order_line.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                line._compute_amount()
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            if order.global_discount_type == 'percent':
                order.total_global_discount = (amount_untaxed + amount_tax) * (order.global_order_discount / 100.0)
            if order.global_discount_type == 'fixed':
                order.total_global_discount = order.global_order_discount
            if not order.global_discount_type:
                order.total_global_discount = 0.0
            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax - order.total_global_discount,
            })

    total_global_discount = fields.Monetary(string='Total Global Discount',
        store=True, readonly=True, default=0)
    total_discount = fields.Monetary(string='Discount', store=True, readonly=True, default=0, compute='_amount_discount', tracking=True)
    global_discount_type = fields.Selection([('fixed', 'Fixed'),('percent', 'Percent')],
                                            string="Discount Type", default="percent", tracking=True)
    global_order_discount = fields.Float(string='Global Discount', store=True, tracking=True)
    apply_global_discount = fields.Boolean(string="Apply Global Discount")

    @api.onchange('global_discount_type', 'global_order_discount')
    def _onchange_global_order_discount(self):
        self._amount_all()

    @api.onchange('apply_global_discount')
    def change_apply_global_discount(self):
        if self.apply_global_discount:
            for line in self.order_line:
                line.discount = 0
        else:
            self.global_order_discount = 0

    @api.constrains('global_order_discount', 'order_line.discount')
    def validate_only_one_discount(self):
        for rec in self:
            if any(line.discount > 0 for line in rec.order_line) and rec.global_order_discount > 0:
                raise ValidationError("You can only apply one discount at a time. \n Global discount or line discount")


class PurchaseOrderLineDiscount(models.Model):
    _inherit = "purchase.order.line"

    discount_type = fields.Selection([('fixed', 'Fixed'),
                                      ('percent', 'Percent')],
                                     string="Discount Type", default="percent")
    is_global_line = fields.Boolean(string='Global Discount Line',
        help="This field is used to separate global discount line.")

    discount = fields.Float("Discount")


    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            vals = line._prepare_compute_all_values()
            if line.discount_type == 'percent' or not line.discount_type:
                vals['price_unit'] = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if line.discount_type == 'fixed':
                vals['price_unit'] = line.price_unit - line.discount
            taxes = line.taxes_id.compute_all(
                vals['price_unit'],
                vals['currency_id'],
                vals['product_qty'],
                vals['product'],
                vals['partner'])
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    def _prepare_account_move_line(self, move=False):
        self.ensure_one()
        res = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': '%s: %s' % (self.order_id.name, self.name),
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'price_unit': self.price_unit,
            'discount_type': self.discount_type,
            'discount': self.discount,
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'analytic_account_id': self.account_analytic_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'purchase_line_id': self.id,
        }
        if not move:
            return res

        if self.currency_id == move.company_id.currency_id:
            currency = False
        else:
            currency = move.currency_id

        res.update({
            'move_id': move.id,
            'currency_id': currency and currency.id or False,
            'date_maturity': move.invoice_date_due,
            'partner_id': move.partner_id.id,
        })
        return res