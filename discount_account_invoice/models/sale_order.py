# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrderDiscount(models.Model):
    _inherit = "sale.order"
    

    @api.depends('order_line.price_total', 'order_line.discount', 'order_line.product_uom_qty')
    def _amount_discount(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            discount = 0.0
            for line in order.order_line:
                discount += line.discount if line.discount_type == 'fixed' else line.product_uom_qty * line.price_unit * line.discount / 100.0
            #order.update({
                #'total_discount': discount,
            #})
            order.total_discount = discount + order.total_global_discount

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            if order.global_discount_type == 'percent':
                order.total_global_discount = (amount_untaxed + amount_tax) * (order.global_order_discount / 100.0)
            if order.global_discount_type == 'fixed':
                order.total_global_discount = order.global_order_discount
            if not order.global_discount_type:
                order.total_global_discount = 0.0
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax - order.total_global_discount,
            })


    total_global_discount = fields.Monetary(string='Total Global Discount',
        store=True, readonly=True, default=0)
    total_discount = fields.Monetary(string='Discount', store=True, readonly=True, default=0, compute='_amount_discount', tracking=True)
    global_discount_type = fields.Selection([('fixed', 'Fixed'),('percent', 'Percent')], string="Discount Type", default="percent", tracking=True)
    global_order_discount = fields.Float(string='Global Discount', store=True, tracking=True)
    apply_global_discount = fields.Boolean(string="Apply Global Discount")

    @api.onchange('global_discount_type', 'global_order_discount')
    def _onchange_global_order_discount(self):
        self._amount_all()
        self._amount_discount()

    @api.constrains('global_order_discount', 'order_line.discount')
    def validate_only_one_discount(self):
        for rec in self:
            if any(line.discount > 0 for line in rec.order_line) and rec.global_order_discount > 0:
                raise ValidationError("You can only apply one discount at a time. \n Global discount or line discount")


    @api.onchange('apply_global_discount')
    def change_apply_global_discount(self):
        if self.apply_global_discount:
            for line in self.order_line:
                line.discount = 0
        else:
            self.global_order_discount = 0


class SaleOrderLineDiscount(models.Model):
    _inherit = "sale.order.line"

    discount_type = fields.Selection([('fixed', 'Fixed'),
                                      ('percent', 'Percent')],
                                     string="Discount Type", default="percent")
    is_global_line = fields.Boolean(string='Global Discount Line',
        help="This field is used to separate global discount line.")


    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            if line.discount_type == 'percent' or not line.discount_type:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if line.discount_type == 'fixed':
                price = line.price_unit - line.discount
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

    def _prepare_invoice_line(self, **optional_values):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        :param optional_values: any parameter that should be added to the returned invoice line
        """
        self.ensure_one()
        res = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'discount_type': self.discount_type,
            'tax_ids': [(6, 0, self.tax_id.ids)],
            'analytic_account_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'sale_line_ids': [(4, self.id)],
        }
        if optional_values:
            res.update(optional_values)
        if self.display_type:
            res['account_id'] = False
        return res