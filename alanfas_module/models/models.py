# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class delivaryDate(models.Model):
    _name = 'dilvevery.date'
    delevery_date = fields.Date(string="تاريخ التسليم", required=False, )
    product_id_1 = fields.Many2one('product.product', "Product")
    qty = fields.Integer('Qty')
    sale_id = fields.Many2one(comodel_name="sale.order", string="sale", required=False, )
    po_id = fields.Many2one(comodel_name="purchase.order", string="PO", required=False, )


# so
class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    anfas_cost = fields.Float(string="التكلفه", required=False, )
    delevery_date = fields.One2many(comodel_name="dilvevery.date", inverse_name="sale_id", string="", required=False, )
    driver_name = fields.Char(string="اسم السائق", required=False, )
    car_number = fields.Char(string="رقم السياره", required=False, )
    customer_phone = fields.Char(string="رقم هاتف الزبون", required=False, size=12)
    customer_adress = fields.Char(string="عنوان الزبون", required=False, )
    omola_cost = fields.Float(string="العموله", required=False, )
    omola_debit_account_id = fields.Many2one('account.account', string="Depit Account", required=True,
                                             domain="[('company_id', '=', company_id)]", )

    omola_credit_account_id = fields.Many2one('account.account', string="Credit Account", required=True,
                                              domain="[('company_id', '=', company_id)]")
    omola_entry = fields.Many2one('account.move', string="قيد العموله", readonly=True, copy=False, )
    cost_debit_account_id = fields.Many2one('account.account', string="Depit Account", required=True,
                                            domain="[('company_id', '=', company_id)]",
                                            )
    cost_credit_account_id = fields.Many2one('account.account', string="Credit Account", required=True,
                                             domain="[('company_id', '=', company_id)]")
    cost_entry = fields.Many2one('account.move', string="قيد التكلفه", readonly=True, copy=False, )

    def action_confirm(self):
        if self.omola_cost:
            move = self.env['account.move'].create({
                'move_type': 'entry',
                'date': self.date_order,
                'ref': 'عموله',
                'line_ids': [
                    (0, 0, {
                        'account_id': self.omola_debit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': self.omola_cost,
                        'credit': 0.0,
                        'partner_id': self.partner_id.id,

                    }),
                    (0, 0, {
                        'account_id': self.omola_credit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': 0.0,
                        'credit': self.omola_cost,
                        'partner_id': self.partner_id.id,
                    }),

                ],
            })
        if self.omola_cost:
            if move:
                self.omola_entry = move.id
            else:
                self.omola_entry = False
        if self.anfas_cost:
            move = self.env['account.move'].create({
                'move_type': 'entry',
                'date': self.date_order,
                'ref': 'تكلفه',
                'line_ids': [
                    (0, 0, {
                        'account_id': self.cost_debit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': self.anfas_cost,
                        'credit': 0.0,
                        'partner_id': self.partner_id.id,

                    }),
                    (0, 0, {
                        'account_id': self.cost_credit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': 0.0,
                        'credit': self.anfas_cost,
                        'partner_id': self.partner_id.id,
                    }),

                ],
            })
        if self.anfas_cost:
            if move:
                self.cost_entry = move.id
            else:
                self.cost_entry = False

        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write(self._prepare_confirmation_values())
        self._action_confirm()
        if self.env.user.has_group('sale.group_auto_done_setting'):
            self.action_done()
        return True

    @api.depends('partner_id')
    @api.onchange('partner_id')
    def compute_default_account(self):

        account_debit = self.env['account.account'].search(
            [('code', '=', '503000'), ('company_id', '=', self.company_id.id)])
        cost_account_debit = self.env['account.account'].search(
            [('code', '=', '110321'), ('company_id', '=', self.company_id.id)])

        account_credit = self.env['account.account'].search(
            [('code', '=', '120010'), ('company_id', '=', self.company_id.id)])
        cost_account_credit = self.env['account.account'].search(
            [('code', '=', '120010'), ('company_id', '=', self.company_id.id)])
        # print(account)
        if account_debit:
            self.omola_debit_account_id = account_debit.id

        else:
            self.omola_debit_account_id = False
        if account_credit:
            self.omola_credit_account_id = account_credit.id
        else:
            self.omola_credit_account_id = False

        if cost_account_debit:
            self.cost_debit_account_id = cost_account_debit.id
        else:
            self.cost_debit_account_id = False
        if cost_account_credit:
            self.cost_credit_account_id = cost_account_credit.id
        else:
            self.cost_credit_account_id = False

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (
                self.company_id.name, self.company_id.id))

        invoice_vals = {
            'ref': self.client_order_ref or '',
            'move_type': 'out_invoice',
            'narration': self.note,
            'currency_id': self.pricelist_id.currency_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'source_id': self.source_id.id,
            'invoice_user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id,
            'delevery_date': self.delevery_date,
            'anfas_cost': self.anfas_cost,
            'car_number': self.car_number,
            'driver_name': self.driver_name,
            'customer_adress': self.customer_adress,
            'customer_phone': self.customer_phone,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(
                self.partner_invoice_id.id)).id,
            'partner_bank_id': self.company_id.partner_id.bank_ids[:1].id,
            'journal_id': journal.id,  # company comes from the journal
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'payment_reference': self.reference,
            'transaction_ids': [(6, 0, self.transaction_ids.ids)],
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
        }
        return invoice_vals

    # @api.onchange('anfas_cost' )
    # def onchange_anfas_cost(self):
    #     if self.amount_total != 0:
    #         cost1 = self.anfas_cost/self.amount_total
    #         for rec in self.order_line:
    #             if cost1 != 0 :
    #                 rec.price_unit = rec.price_unit * cost1 +rec.price_unit
    #             # else:
    #             #     rec.price_unit = rec.product_id.lst_price


# so_line
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    real_price_unit = fields.Float('Real Unit Price', required=True, digits='Product Price', default=0.0)

    @api.onchange('product_id')
    def onchange_method(self):
        self.price_unit = self.product_id.lst_price
        self.real_price_unit = self.product_id.lst_price


# po
class PurchaseOrderInherit(models.Model):
    _inherit = "purchase.order"

    anfas_cost = fields.Float(string="التكلفه", required=False, )
    total_real_cost = fields.Float(string="Total Real price", required=False, compute="_compute_total_real_cost")

    delevery_date = fields.One2many(comodel_name="dilvevery.date", inverse_name="po_id", string="", required=False, )
    cost_debit_account_id = fields.Many2one('account.account', string="Depit Account", required=True,
                                            domain="[('company_id', '=', company_id)]",
                                            compute="compute_default_account")
    cost_credit_account_id = fields.Many2one('account.account', string="Credit Account", required=True,
                                             domain="[('company_id', '=', company_id)]")
    cost_entry = fields.Many2one('account.move', string="قيد التكلفه", readonly=True, copy=False, )
    # omola for purchase
    omola_cost = fields.Float(string="العموله", required=False, )
    omola_debit_account_id = fields.Many2one('account.account', string="Depit Account", required=False,
                                             domain="[('company_id', '=', company_id)]", )

    omola_credit_account_id = fields.Many2one('account.account', string="Credit Account", required=False,
                                              domain="[('company_id', '=', company_id)]")
    omola_entry = fields.Many2one('account.move', string="قيد العموله", readonly=True, copy=False, )

    internal_transfer_cost = fields.Float(string="تكلفه نقل داخلي", required=False, )
    omola_transfer_cost = fields.Float(string=" تكلفه عمولة الحوالات", required=False, )
    gomrky_cost = fields.Float(string=" تكلفه تخليص كمركي", required=False, )
    bhry_cost = fields.Float(string=" تكلفه نقل بحري", required=False, )

    tfreegh = fields.Float(string=" تكلفه أخرى", required=False, )
    okhra = fields.Float(string=" تكلفه مصاريف تفريغ", required=False, )

    # without entry
    no_internal_transfer_cost = fields.Float(string="تكلفه نقل داخلي غير مستحقه", required=False, )
    no_omola_transfer_cost = fields.Float(string=" تكلفه عمولة الحوالات غير مستحقه", required=False, )
    no_gomrky_cost = fields.Float(string=" تكلفه تخليص كمركي غير مستحقه", required=False, )
    no_bhry_cost = fields.Float(string=" تكلفه نقل بحري غير مستحقه", required=False, )
    no_tfreegh = fields.Float(string=" تكاليف أخرى غير مستحقه", required=False, )
    no_okhra = fields.Float(string=" تكلفه مصاريف تفريغ غير مستحقه", required=False, )

    #

    # 4*2 fields  debit and credit >> 8
    internal_transfer_debit_account_id = fields.Many2one('account.account', string="internal_transfer_debit_account_id",
                                                         required=True, compute="compute_default_account",
                                                         domain="[('company_id', '=', company_id)]", )
    internal_transfer_credit_account_id = fields.Many2one('account.account',
                                                          string="internal_transfer_credit_account_id", required=True,
                                                          compute="compute_default_account",
                                                          domain="[('company_id', '=', company_id)]", )
    internal_transfer_entry1 = fields.Many2one('account.move', string="قيد نقل داخلي", readonly=True, copy=False, )

    omola_transfer_debit_account_id = fields.Many2one('account.account', string="omola_transfer_debit_account_id",
                                                      required=True, compute="compute_default_account",
                                                      domain="[('company_id', '=', company_id)]", )

    omola_transfer_credit_account_id = fields.Many2one('account.account', string="omola_transfer_credit_account_id",
                                                       required=True, compute="compute_default_account",
                                                       domain="[('company_id', '=', company_id)]", )

    internal_transfer_entry2 = fields.Many2one('account.move', string="قيد عمولة الحوالات", readonly=True, copy=False, )

    gomrky_debit_account_id = fields.Many2one('account.account', string="gomrky_debit_account_id",
                                              required=True, compute="compute_default_account",
                                              domain="[('company_id', '=', company_id)]", )
    gomrky_transfer_credit_account_id = fields.Many2one('account.account',
                                                        string="gomrky_transfer_credit_account_id", required=True,
                                                        compute="compute_default_account",
                                                        domain="[('company_id', '=', company_id)]", )
    internal_transfer_entry3 = fields.Many2one('account.move', string="قيد تخليص كمركي", readonly=True, copy=False, )

    bhry_transfer_debit_account_id = fields.Many2one('account.account', string="bhry_transfer_debit_account_id",
                                                     required=True, compute="compute_default_account",
                                                     domain="[('company_id', '=', company_id)]", )

    bhry_transfer_credit_account_id = fields.Many2one('account.account', string="bhry_transfer_credit_account_id",
                                                      required=True, compute="compute_default_account",
                                                      domain="[('company_id', '=', company_id)]", )
    internal_transfer_entry4 = fields.Many2one('account.move', string="قيد نقل بحري", readonly=True, copy=False, )

    # مصاريف تفريغ مستحقه
    tfreegh_debit_account_id = fields.Many2one('account.account', string="tfreegh_debit_account_id",
                                                 required=True, compute="compute_default_account",
                                                 domain="[('company_id', '=', company_id)]", )
    tfreegh_credit_account_id = fields.Many2one('account.account',
                                                           string="tfreegh_credit_account_id", required=True,
                                                           compute="compute_default_account",
                                                           domain="[('company_id', '=', company_id)]", )
    tfreegh_entry5 = fields.Many2one('account.move', string="قيد مصاريف تفريغ", readonly=True, copy=False, )

    okhra_debit_account_id = fields.Many2one('account.account', string="okhra_debit_account_id",
                                                        required=True, compute="compute_default_account",
                                                        domain="[('company_id', '=', company_id)]", )

    okhra_credit_account_id = fields.Many2one('account.account', string="okhra_credit_account_id",
                                                         required=True, compute="compute_default_account",
                                                         domain="[('company_id', '=', company_id)]", )
    okhra_entry6 = fields.Many2one('account.move', string="قيد تكاليف أخري", readonly=True, copy=False, )

    #
    # the first 6 accounts end
    # the first 6 accounts end
    # the first 6 accounts end
    # the first 6 accounts end
    # the first 6 accounts end
    no_internal_transfer_debit_account_id = fields.Many2one('account.account',
                                                            string="internal_transfer_debit_account_id",
                                                            required=True, compute="compute_default_account",
                                                            domain="[('company_id', '=', company_id)]", )
    no_internal_transfer_credit_account_id = fields.Many2one('account.account',
                                                             string="internal_transfer_credit_account_id",
                                                             required=True,
                                                             compute="compute_default_account",
                                                             domain="[('company_id', '=', company_id)]", )
    no_internal_transfer_entry1 = fields.Many2one('account.move', string="قيد نقل داخلي", readonly=True, copy=False, )

    no_omola_transfer_debit_account_id = fields.Many2one('account.account', string="omola_transfer_debit_account_id",
                                                         required=True, compute="compute_default_account",
                                                         domain="[('company_id', '=', company_id)]", )

    no_omola_transfer_credit_account_id = fields.Many2one('account.account', string="omola_transfer_credit_account_id",
                                                          required=True, compute="compute_default_account",
                                                          domain="[('company_id', '=', company_id)]", )

    no_internal_transfer_entry2 = fields.Many2one('account.move', string="قيد عمولة الحوالات", readonly=True,
                                                  copy=False, )

    no_gomrky_debit_account_id = fields.Many2one('account.account', string="gomrky_debit_account_id",
                                                 required=True, compute="compute_default_account",
                                                 domain="[('company_id', '=', company_id)]", )
    no_gomrky_transfer_credit_account_id = fields.Many2one('account.account',
                                                           string="gomrky_transfer_credit_account_id", required=True,
                                                           compute="compute_default_account",
                                                           domain="[('company_id', '=', company_id)]", )
    no_internal_transfer_entry3 = fields.Many2one('account.move', string="قيد تخليص كمركي", readonly=True, copy=False, )

    no_bhry_transfer_debit_account_id = fields.Many2one('account.account', string="bhry_transfer_debit_account_id",
                                                        required=True, compute="compute_default_account",
                                                        domain="[('company_id', '=', company_id)]", )

    no_bhry_transfer_credit_account_id = fields.Many2one('account.account', string="bhry_transfer_credit_account_id",
                                                         required=True, compute="compute_default_account",
                                                         domain="[('company_id', '=', company_id)]", )
    no_internal_transfer_entry4 = fields.Many2one('account.move', string="قيد نقل بحري", readonly=True, copy=False, )

    # مصاريف تفريغ غير مستحقه

    no_tfreegh_debit_account_id = fields.Many2one('account.account', string="no_tfreegh_debit_account_id",
                                                 required=True, compute="compute_default_account",
                                                 domain="[('company_id', '=', company_id)]", )
    no_tfreegh_credit_account_id = fields.Many2one('account.account',
                                                           string="no_tfreegh_credit_account_id", required=True,
                                                           compute="compute_default_account",
                                                           domain="[('company_id', '=', company_id)]", )
    no_tfreegh_entry5 = fields.Many2one('account.move', string="قيد مصاريف التفريغ غير مستحق", readonly=True, copy=False, )

    no_okhra_debit_account_id = fields.Many2one('account.account', string="no_okhra_debit_account_id",
                                                        required=True, compute="compute_default_account",
                                                        domain="[('company_id', '=', company_id)]", )

    no_okhra_credit_account_id = fields.Many2one('account.account', string="no_okhra_credit_account_id",
                                                         required=True, compute="compute_default_account",
                                                         domain="[('company_id', '=', company_id)]", )
    no_okhra_entry6 = fields.Many2one('account.move', string="قيد تكاليف أخري غير مستحقه", readonly=True, copy=False, )

    #
    #
    # old function work with multi steps as odoo default business cycle
    # def button_confirm(self):
    #     if self.omola_cost:
    #         move_omola_cost = self.env['account.move'].create({
    #             'move_type': 'entry',
    #             'date': self.date_order,
    #             'ref': 'عموله',
    #             'line_ids': [
    #                 (0, 0, {
    #                     'account_id': self.omola_debit_account_id.id,
    #                     # 'currency_id': self.currency_data['currency'].id,
    #                     'debit': self.omola_cost,
    #                     'credit': 0.0,
    #                     'partner_id': self.partner_id.id,
    #                     'name': "العموله",
    #
    #                 }),
    #                 (0, 0, {
    #                     'account_id': self.omola_credit_account_id.id,
    #                     # 'currency_id': self.currency_data['currency'].id,
    #                     'debit': 0.0,
    #                     'credit': self.omola_cost,
    #                     'partner_id': self.partner_id.id,
    #                     'name': "العموله",
    #                 }),
    #
    #             ],
    #         })
    #     if self.omola_cost:
    #         if move_omola_cost:
    #             self.omola_entry = move_omola_cost.id
    #         else:
    #             self.omola_entry = False
    #
    #     if self.anfas_cost:
    #         move = self.env['account.move'].create({
    #             'move_type': 'entry',
    #             'date': self.date_order,
    #             'ref': 'تكلفه',
    #             'line_ids': [
    #                 (0, 0, {
    #                     'account_id': self.cost_debit_account_id.id,
    #                     # 'currency_id': self.currency_data['currency'].id,
    #                     'debit': self.anfas_cost,
    #                     'credit': 0.0,
    #                     'partner_id': self.partner_id.id,
    #                     'name': "التكلفه",
    #                 }),
    #                 (0, 0, {
    #                     'account_id': self.cost_credit_account_id.id,
    #                     # 'currency_id': self.currency_data['currency'].id,
    #                     'debit': 0.0,
    #                     'credit': self.anfas_cost,
    #                     'partner_id': self.partner_id.id,
    #                     'name': "التكلفه",
    #                 }),
    #
    #             ],
    #         })
    #     if self.anfas_cost:
    #         if move:
    #             self.cost_entry = move.id
    #         else:
    #             self.cost_entry = False
    #     #
    #     # 4 entries
    #     #
    #     # 1
    #     if self.internal_transfer_cost:
    #         move_internal_transfer_cost = self.env['account.move'].create({
    #             'move_type': 'entry',
    #             'date': self.date_order,
    #             'ref': 'نقل داخلي',
    #             'line_ids': [
    #                 (0, 0, {
    #                     'account_id': self.internal_transfer_debit_account_id.id,
    #                     # 'currency_id': self.currency_data['currency'].id,
    #                     'debit': self.internal_transfer_cost,
    #                     'credit': 0.0,
    #                     'partner_id': self.partner_id.id,
    #                     'name': "نقل داخلي",
    #
    #                 }),
    #                 (0, 0, {
    #                     'account_id': self.internal_transfer_credit_account_id.id,
    #                     # 'currency_id': self.currency_data['currency'].id,
    #                     'debit': 0.0,
    #                     'credit': self.internal_transfer_cost,
    #                     'partner_id': self.partner_id.id,
    #                     'name': "نقل داخلي",
    #                 }),
    #
    #             ],
    #         })
    #     if self.internal_transfer_cost:
    #         if move_internal_transfer_cost:
    #             self.internal_transfer_entry1 = move_internal_transfer_cost.id
    #         else:
    #             self.internal_transfer_entry1 = False
    #     #
    #     # 2
    #     if self.omola_transfer_cost:
    #         omola_transfer_cost_move = self.env['account.move'].create({
    #             'move_type': 'entry',
    #             'date': self.date_order,
    #             'ref': 'عمولة الحوالات',
    #             'line_ids': [
    #                 (0, 0, {
    #                     'account_id': self.omola_transfer_debit_account_id.id,
    #                     # 'currency_id': self.currency_data['currency'].id,
    #                     'debit': self.omola_transfer_cost,
    #                     'credit': 0.0,
    #                     'partner_id': self.partner_id.id,
    #                     'name': "عمولة الحوالات",
    #
    #                 }),
    #                 (0, 0, {
    #                     'account_id': self.omola_transfer_credit_account_id.id,
    #                     # 'currency_id': self.currency_data['currency'].id,
    #                     'debit': 0.0,
    #                     'credit': self.omola_transfer_cost,
    #                     'partner_id': self.partner_id.id,
    #                     'name': "عمولة الحوالات",
    #                 }),
    #
    #             ],
    #         })
    #     if self.omola_transfer_cost:
    #         if omola_transfer_cost_move:
    #             self.internal_transfer_entry2 = omola_transfer_cost_move.id
    #         else:
    #             self.internal_transfer_entry2 = False
    #     #
    #     # 3
    #     if self.gomrky_cost:
    #         gomrky_cost_move = self.env['account.move'].create({
    #             'move_type': 'entry',
    #             'date': self.date_order,
    #             'ref': 'تخليص كمركي',
    #             'line_ids': [
    #                 (0, 0, {
    #                     'account_id': self.gomrky_debit_account_id.id,
    #                     # 'currency_id': self.currency_data['currency'].id,
    #                     'debit': self.gomrky_cost,
    #                     'credit': 0.0,
    #                     'partner_id': self.partner_id.id,
    #                     'name': "تخليص كمركي",
    #
    #                 }),
    #                 (0, 0, {
    #                     'account_id': self.gomrky_transfer_credit_account_id.id,
    #                     # 'currency_id': self.currency_data['currency'].id,
    #                     'debit': 0.0,
    #                     'credit': self.gomrky_cost,
    #                     'partner_id': self.partner_id.id,
    #                     'name': "تخليص كمركي",
    #                 }),
    #
    #             ],
    #         })
    #     if self.gomrky_cost:
    #         if gomrky_cost_move:
    #             self.internal_transfer_entry3 = gomrky_cost_move.id
    #         else:
    #             self.internal_transfer_entry3 = False
    #
    #     #
    #     # 4
    #     if self.bhry_cost:
    #         bhry_cost_move = self.env['account.move'].create({
    #             'move_type': 'entry',
    #             'date': self.date_order,
    #             'ref': 'نقل بحري',
    #             'line_ids': [
    #                 (0, 0, {
    #                     'account_id': self.bhry_transfer_debit_account_id.id,
    #                     # 'currency_id': self.currency_data['currency'].id,
    #                     'debit': self.bhry_cost,
    #                     'credit': 0.0,
    #                     'partner_id': self.partner_id.id,
    #                     'name': "نقل بحري",
    #
    #                 }),
    #                 (0, 0, {
    #                     'account_id': self.bhry_transfer_credit_account_id.id,
    #                     # 'currency_id': self.currency_data['currency'].id,
    #                     'debit': 0.0,
    #                     'credit': self.bhry_cost,
    #                     'partner_id': self.partner_id.id,
    #                     'name': "نقل بحري",
    #                 }),
    #
    #             ],
    #         })
    #     if self.bhry_cost:
    #         if bhry_cost_move:
    #             self.internal_transfer_entry4 = bhry_cost_move.id
    #         else:
    #             self.internal_transfer_entry4 = False
    #     #
    #
    #     for order in self:
    #         if order.state not in ['draft', 'sent']:
    #             continue
    #         order._add_supplier_to_product()
    #         # Deal with double validation process
    #         if order.company_id.po_double_validation == 'one_step' \
    #                 or (order.company_id.po_double_validation == 'two_step' \
    #                     and order.amount_total < self.env.company.currency_id._convert(
    #                     order.company_id.po_double_validation_amount, order.currency_id, order.company_id,
    #                     order.date_order or fields.Date.today())) \
    #                 or order.user_has_groups('purchase.group_purchase_manager'):
    #             order.button_approve()
    #         else:
    #             order.write({'state': 'to approve'})
    #         if order.partner_id not in order.message_partner_ids:
    #             order.message_subscribe([order.partner_id.id])
    #     return True
    #     # old function work with one step po business cycle changed
    # for confirm po one step cycle
    def button_confirms(self):
        # start of all entries
        res = super(PurchaseOrderInherit, self).button_confirm()
        # cost and omola entries deleted based request from ahmed karim
        # if self.omola_cost:
        #     move_omola_cost = self.env['account.move'].create({
        #         'move_type': 'entry',
        #         'date': self.date_order,
        #         'ref': 'عموله',
        #         'line_ids': [
        #             (0, 0, {
        #                 'account_id': self.omola_debit_account_id.id,
        #                 # 'currency_id': self.currency_data['currency'].id,
        #                 'debit': self.omola_cost,
        #                 'credit': 0.0,
        #                 'partner_id': self.partner_id.id,
        #                 'name': "العموله",
        #
        #             }),
        #             (0, 0, {
        #                 'account_id': self.omola_credit_account_id.id,
        #                 # 'currency_id': self.currency_data['currency'].id,
        #                 'debit': 0.0,
        #                 'credit': self.omola_cost,
        #                 'partner_id': self.partner_id.id,
        #                 'name': "العموله",
        #             }),
        #
        #         ],
        #     })
        # if self.omola_cost:
        #     if move_omola_cost:
        #         self.omola_entry = move_omola_cost.id
        #     else:
        #         self.omola_entry = False
        #
        # if self.anfas_cost:
        #     move = self.env['account.move'].create({
        #         'move_type': 'entry',
        #         'date': self.date_order,
        #         'ref': 'تكلفه',
        #         'line_ids': [
        #             (0, 0, {
        #                 'account_id': self.cost_debit_account_id.id,
        #                 # 'currency_id': self.currency_data['currency'].id,
        #                 'debit': self.anfas_cost,
        #                 'credit': 0.0,
        #                 'partner_id': self.partner_id.id,
        #                 'name': "التكلفه",
        #             }),
        #             (0, 0, {
        #                 'account_id': self.cost_credit_account_id.id,
        #                 # 'currency_id': self.currency_data['currency'].id,
        #                 'debit': 0.0,
        #                 'credit': self.anfas_cost,
        #                 'partner_id': self.partner_id.id,
        #                 'name': "التكلفه",
        #             }),
        #
        #         ],
        #     })
        # if self.anfas_cost:
        #     if move:
        #         self.cost_entry = move.id
        #     else:
        #         self.cost_entry = False

        #     # 4 entries
        #     #
        #     # 1
        if self.internal_transfer_cost:
            move_internal_transfer_cost = self.env['account.move'].create({
                'move_type': 'entry',
                'date': self.date_order,
                # 'state': 'posted',
                'ref': 'نقل داخلي',
                'line_ids': [
                    (0, 0, {
                        'account_id': self.internal_transfer_debit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': self.internal_transfer_cost,
                        'credit': 0.0,
                        'partner_id': self.partner_id.id,
                        'name': "نقل داخلي",

                    }),
                    (0, 0, {
                        'account_id': self.internal_transfer_credit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': 0.0,
                        'credit': self.internal_transfer_cost,
                        'partner_id': self.partner_id.id,
                        'name': "نقل داخلي",
                    }),

                ],
            })
        if self.internal_transfer_cost:
            if move_internal_transfer_cost:
                self.internal_transfer_entry1 = move_internal_transfer_cost.id
            else:
                self.internal_transfer_entry1 = False
            #
            # 2
        if self.omola_transfer_cost:
            omola_transfer_cost_move = self.env['account.move'].create({
                'move_type': 'entry',
                'date': self.date_order,
                'ref': 'عمولة الحوالات',
                'line_ids': [
                    (0, 0, {
                        'account_id': self.omola_transfer_debit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': self.omola_transfer_cost,
                        'credit': 0.0,
                        'partner_id': self.partner_id.id,
                        'name': "عمولة الحوالات",

                    }),
                    (0, 0, {
                        'account_id': self.omola_transfer_credit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': 0.0,
                        'credit': self.omola_transfer_cost,
                        'partner_id': self.partner_id.id,
                        'name': "عمولة الحوالات",
                    }),

                ],
            })
        if self.omola_transfer_cost:
            if omola_transfer_cost_move:
                self.internal_transfer_entry2 = omola_transfer_cost_move.id
            else:
                self.internal_transfer_entry2 = False
            #
            # 3
        if self.gomrky_cost:
            gomrky_cost_move = self.env['account.move'].create({
                'move_type': 'entry',
                'date': self.date_order,
                'ref': 'تخليص كمركي',
                'line_ids': [
                    (0, 0, {
                        'account_id': self.gomrky_debit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': self.gomrky_cost,
                        'credit': 0.0,
                        'partner_id': self.partner_id.id,
                        'name': "تخليص كمركي",

                    }),
                    (0, 0, {
                        'account_id': self.gomrky_transfer_credit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': 0.0,
                        'credit': self.gomrky_cost,
                        'partner_id': self.partner_id.id,
                        'name': "تخليص كمركي",
                    }),

                ],
            })
        if self.gomrky_cost:
            if gomrky_cost_move:
                self.internal_transfer_entry3 = gomrky_cost_move.id
            else:
                self.internal_transfer_entry3 = False

            #
            # 4
        if self.bhry_cost:
            bhry_cost_move = self.env['account.move'].create({
                'move_type': 'entry',
                'date': self.date_order,
                'ref': 'نقل بحري',
                'line_ids': [
                    (0, 0, {
                        'account_id': self.bhry_transfer_debit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': self.bhry_cost,
                        'credit': 0.0,
                        'partner_id': self.partner_id.id,
                        'name': "نقل بحري",

                    }),
                    (0, 0, {
                        'account_id': self.bhry_transfer_credit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': 0.0,
                        'credit': self.bhry_cost,
                        'partner_id': self.partner_id.id,
                        'name': "نقل بحري",
                    }),

                ],
            })
        if self.bhry_cost:
            if bhry_cost_move:
                self.internal_transfer_entry4 = bhry_cost_move.id
            else:
                self.internal_transfer_entry4 = False
        #
        #5
        if self.tfreegh:
            tfreegh_cost_move = self.env['account.move'].create({
                'move_type': 'entry',
                'date': self.date_order,
                'ref': 'تكلفه مصاريف تفريغ',
                'line_ids': [
                    (0, 0, {
                        'account_id': self.tfreegh_debit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': self.tfreegh,
                        'credit': 0.0,
                        'partner_id': self.partner_id.id,
                        'name': "تكلفه مصاريف تفريغ",

                    }),
                    (0, 0, {
                        'account_id': self.tfreegh_credit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': 0.0,
                        'credit': self.tfreegh,
                        'partner_id': self.partner_id.id,
                        'name': "تكلفه مصاريف تفريغ",
                    }),

                ],
            })
        if self.tfreegh:
            if tfreegh_cost_move:
                self.tfreegh_entry5 = tfreegh_cost_move.id
            else:
                self.tfreegh_entry5 = False
        #
        # 6
        if self.okhra:
            okhra_cost_move = self.env['account.move'].create({
                'move_type': 'entry',
                'date': self.date_order,
                'ref': 'تكاليف أخري',
                'line_ids': [
                    (0, 0, {
                        'account_id': self.okhra_debit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': self.okhra,
                        'credit': 0.0,
                        'partner_id': self.partner_id.id,
                        'name': "تكاليف أخري",

                    }),
                    (0, 0, {
                        'account_id': self.okhra_credit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': 0.0,
                        'credit': self.okhra,
                        'partner_id': self.partner_id.id,
                        'name': "تكاليف أخري",
                    }),

                ],
            })
        if self.okhra:
            if okhra_cost_move:
                self.okhra_entry6 = okhra_cost_move.id
            else:
                self.okhra_entry6 = False
        # end of entries التكاليف المستحقه
        # end of entries التكاليف المستحقه
        # end of entries التكاليف المستحقه
        # end of entries التكاليف المستحقه
        #     #
        #     # 1
        if self.internal_transfer_cost:
            no_move_internal_transfer_cost = self.env['account.move'].create({
                'move_type': 'entry',
                'date': self.date_order,
                'ref': 'نقل داخلي غير مستحق',
                'line_ids': [
                    (0, 0, {
                        'account_id': self.no_internal_transfer_debit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': self.no_internal_transfer_cost,
                        'credit': 0.0,
                        'partner_id': self.partner_id.id,
                        'name': "نقل داخلي غير مستحق",

                    }),
                    (0, 0, {
                        'account_id': self.no_internal_transfer_credit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': 0.0,
                        'credit': self.no_internal_transfer_cost,
                        'partner_id': self.partner_id.id,
                        'name': "نقل داخلي غير مستحق",
                    }),

                ],
            })
        if self.no_internal_transfer_cost:
            if no_move_internal_transfer_cost:
                self.no_internal_transfer_entry1 = no_move_internal_transfer_cost.id
            else:
                self.no_internal_transfer_entry1 = False
            #
            # 2
        #
        # 2
        if self.no_omola_transfer_cost:
            no_omola_transfer_cost_move = self.env['account.move'].create({
                'move_type': 'entry',
                'date': self.date_order,
                'ref': 'عمولة الحوالات غير مستحق',
                'line_ids': [
                    (0, 0, {
                        'account_id': self.no_omola_transfer_debit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': self.no_omola_transfer_cost,
                        'credit': 0.0,
                        'partner_id': self.partner_id.id,
                        'name': "عمولة الحوالات غير مستحق",

                    }),
                    (0, 0, {
                        'account_id': self.no_omola_transfer_credit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': 0.0,
                        'credit': self.no_omola_transfer_cost,
                        'partner_id': self.partner_id.id,
                        'name': "عمولة الحوالات غير مستحق",
                    }),

                ],
            })
        if self.no_omola_transfer_cost:
            if no_omola_transfer_cost_move:
                self.no_internal_transfer_entry2 = no_omola_transfer_cost_move.id
            else:
                self.no_internal_transfer_entry2 = False
        #
        # 3
        if self.no_gomrky_cost:
            no_gomrky_cost_move = self.env['account.move'].create({
                'move_type': 'entry',
                'date': self.date_order,
                'ref': 'تخليص كمركي غير مستحق',
                'line_ids': [
                    (0, 0, {
                        'account_id': self.no_gomrky_debit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': self.no_gomrky_cost,
                        'credit': 0.0,
                        'partner_id': self.partner_id.id,
                        'name': "تخليص كمركي غير مستحق",

                    }),
                    (0, 0, {
                        'account_id': self.no_gomrky_transfer_credit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': 0.0,
                        'credit': self.no_gomrky_cost,
                        'partner_id': self.partner_id.id,
                        'name': "تخليص كمركي غير مستحق",
                    }),

                ],
            })
        if self.no_gomrky_cost:
            if no_gomrky_cost_move:
                self.no_internal_transfer_entry3 = no_gomrky_cost_move.id
            else:
                self.no_internal_transfer_entry3 = False

        #
        # 4
        if self.no_bhry_cost:
            no_bhry_cost_move = self.env['account.move'].create({
                'move_type': 'entry',
                'date': self.date_order,
                'ref': 'نقل بحري غير مستحق',
                'line_ids': [
                    (0, 0, {
                        'account_id': self.no_bhry_transfer_debit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': self.no_bhry_cost,
                        'credit': 0.0,
                        'partner_id': self.partner_id.id,
                        'name': "نقل بحري غير مستحق",

                    }),
                    (0, 0, {
                        'account_id': self.no_bhry_transfer_credit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': 0.0,
                        'credit': self.no_bhry_cost,
                        'partner_id': self.partner_id.id,
                        'name': "نقل بحري غير مستحق",
                    }),

                ],
            })
        if self.no_bhry_cost:
            if no_bhry_cost_move:
                self.no_internal_transfer_entry4 = no_bhry_cost_move.id
            else:
                self.no_internal_transfer_entry4 = False

        #
        # 5
        if self.no_tfreegh:
            no_tfreegh_cost_move = self.env['account.move'].create({
                'move_type': 'entry',
                'date': self.date_order,
                'ref': 'تكلفه مصاريف تفريغ غير مستحقه',
                'line_ids': [
                    (0, 0, {
                        'account_id': self.no_tfreegh_debit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': self.no_tfreegh,
                        'credit': 0.0,
                        'partner_id': self.partner_id.id,
                        'name': "تكلفه مصاريف تفريغ غير مستحقه",

                    }),
                    (0, 0, {
                        'account_id': self.no_tfreegh_credit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': 0.0,
                        'credit': self.no_tfreegh,
                        'partner_id': self.partner_id.id,
                        'name': "تكلفه مصاريف تفريغ غير مستحقه",
                    }),

                ],
            })
        if self.no_tfreegh:
            if no_tfreegh_cost_move:
                self.no_tfreegh_entry5 = no_tfreegh_cost_move.id
            else:
                self.no_tfreegh_entry5 = False
        #
        # 6
        if self.no_okhra:
            no_okhra_cost_move = self.env['account.move'].create({
                'move_type': 'entry',
                'date': self.date_order,
                'ref': 'تكاليف أخري غير مستحقه',
                'line_ids': [
                    (0, 0, {
                        'account_id': self.no_okhra_debit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': self.no_okhra,
                        'credit': 0.0,
                        'partner_id': self.partner_id.id,
                        'name': "تكاليف أخري غير مستحقه",

                    }),
                    (0, 0, {
                        'account_id': self.no_okhra_credit_account_id.id,
                        # 'currency_id': self.currency_data['currency'].id,
                        'debit': 0.0,
                        'credit': self.no_okhra,
                        'partner_id': self.partner_id.id,
                        'name': "تكاليف أخري غير مستحقه",
                    }),

                ],
            })
        if self.no_okhra:
            if no_okhra_cost_move:
                self.no_okhra_entry6 = no_okhra_cost_move.id
            else:
                self.no_okhra_entry6 = False

        # end of all cost   entry in added  po
        print("111111111111")
        # imediate_obj = self.env['stock.immediate.transfer']
        warehouse_obj = self.env['stock.warehouse'].search([], limit=1)
        for order in self:
            print("2222222222222")
            warehouse = warehouse_obj
            print(warehouse)
            print("warehouse hafeeeeeeza", warehouse)
            if order.post_deliver_inv_pick and order.picking_ids:
                print("test")
                for picking in order.picking_ids:
                    picking.action_assign()
                    picking.action_confirm()
                    for mv in picking.move_ids_without_package:
                        mv.quantity_done = mv.product_uom_qty
                    picking.button_validate()

            if order.post_deliver_inv_pick and not order.invoice_ids:
                order.action_create_invoice()
            if order.post_deliver_inv_pick and order.invoice_ids:
                for invoice in order.invoice_ids:
                    print("print here msh 3ayez ypost", invoice)
                    invoice.invoice_date = fields.Date.context_today(self)
                    print("invoice.invoice_date", invoice.invoice_date)
                    invoice.action_post()
        return res

    @api.depends('partner_id')
    def compute_default_account(self):

        cost_account_debit = self.env['account.account'].search(
            [('code', '=', '511030'), ('company_id', '=', self.company_id.id)])

        cost_account_credit = self.env['account.account'].search(
            [('code', '=', '110200'), ('company_id', '=', self.company_id.id)])
        # print(account)

        # 1 debit internal
        internal_account_debit = self.env['account.account'].search(
            [('code', '=', '510001'), ('company_id', '=', self.company_id.id)])
        # 1 credit internal
        internal_account_credit = self.env['account.account'].search(
            [('code', '=', '100002'), ('company_id', '=', self.company_id.id)])

        # 2 debit omola_transfer_debit_account_id
        omola_transfer_debit_account = self.env['account.account'].search(
            [('code', '=', '510004'), ('company_id', '=', self.company_id.id)])
        # 2 credit omola_transfer_credit_account_id
        omola_transfer_credit_account = self.env['account.account'].search(
            [('code', '=', '100002'), ('company_id', '=', self.company_id.id)])

        # 3 debit omola_transfer_debit_account_id
        gomrky_debit_account = self.env['account.account'].search(
            [('code', '=', '510002'), ('company_id', '=', self.company_id.id)])
        # 3 credit omola_transfer_credit_account_id
        gomrky_transfer_credit_account = self.env['account.account'].search(
            [('code', '=', '100002'), ('company_id', '=', self.company_id.id)])

        # 4 debit
        bhry_transfer_debit_account = self.env['account.account'].search(
            [('code', '=', '510003'), ('company_id', '=', self.company_id.id)])
        # 4 credit
        bhry_transfer_credit_account = self.env['account.account'].search(
            [('code', '=', '100002'), ('company_id', '=', self.company_id.id)])
        # 5 debit
        tfreegh_debit_account = self.env['account.account'].search(
            [('code', '=', '510006'), ('company_id', '=', self.company_id.id)])
        # 5 credit
        tfreegh_credit_account = self.env['account.account'].search(
            [('code', '=', '100002'), ('company_id', '=', self.company_id.id)])
        # 6 debit
        okra_debit_account = self.env['account.account'].search(
            [('code', '=', '510007'), ('company_id', '=', self.company_id.id)])
        # 6 credit
        okhra_credit_account = self.env['account.account'].search(
            [('code', '=', '100002'), ('company_id', '=', self.company_id.id)])
        # end 4 accounts
        # end 4 accounts
        # end 4 accounts
        # end 4 accounts

        # 1 debit internal
        no_internal_account_debit = self.env['account.account'].search(
            [('code', '=', '200010'), ('company_id', '=', self.company_id.id)])
        # 1 credit internal
        no_internal_account_credit = self.env['account.account'].search(
            [('code', '=', '510005'), ('company_id', '=', self.company_id.id)])

        # 2 debit omola_transfer_debit_account_id
        no_omola_transfer_debit_account = self.env['account.account'].search(
            [('code', '=', '200010'), ('company_id', '=', self.company_id.id)])
        # 2 credit omola_transfer_credit_account_id
        no_omola_transfer_credit_account = self.env['account.account'].search(
            [('code', '=', '510005'), ('company_id', '=', self.company_id.id)])

        # 3 debit omola_transfer_debit_account_id
        no_gomrky_debit_account = self.env['account.account'].search(
            [('code', '=', '200010'), ('company_id', '=', self.company_id.id)])
        # 3 credit omola_transfer_credit_account_id
        no_gomrky_transfer_credit_account = self.env['account.account'].search(
            [('code', '=', '510005'), ('company_id', '=', self.company_id.id)])

        # 4 debit omola_transfer_debit_account_id
        no_bhry_transfer_debit_account = self.env['account.account'].search(
            [('code', '=', '200010'), ('company_id', '=', self.company_id.id)])
        # 4 credit omola_transfer_credit_account_id
        no_bhry_transfer_credit_account = self.env['account.account'].search(
            [('code', '=', '510005'), ('company_id', '=', self.company_id.id)])

        # 5 debit
        no_tfreegh_debit_account = self.env['account.account'].search(
            [('code', '=', '200010'), ('company_id', '=', self.company_id.id)])
        # 5 credit
        no_tfreegh_credit_account = self.env['account.account'].search(
            [('code', '=', '510005'), ('company_id', '=', self.company_id.id)])
        # 6 debit
        no_okra_debit_account = self.env['account.account'].search(
            [('code', '=', '200010'), ('company_id', '=', self.company_id.id)])
        # 6 credit
        no_okhra_credit_account = self.env['account.account'].search(
            [('code', '=', '510005'), ('company_id', '=', self.company_id.id)])

        if cost_account_debit:
            self.cost_debit_account_id = cost_account_debit.id
        else:
            self.cost_debit_account_id = False
        if cost_account_credit:
            self.cost_credit_account_id = cost_account_credit.id
        else:
            self.cost_credit_account_id = False
        # 1 debit internal
        if internal_account_debit:
            self.internal_transfer_debit_account_id = internal_account_debit.id
        else:
            self.internal_transfer_debit_account_id = False
        # 1 credit internal
        if internal_account_credit:
            self.internal_transfer_credit_account_id = internal_account_credit.id
        else:
            self.internal_transfer_credit_account_id = False

        # 2 debit omola_transfer_debit_account_id
        if omola_transfer_debit_account:
            self.omola_transfer_debit_account_id = omola_transfer_debit_account.id
        else:
            self.omola_transfer_debit_account_id = False
        # 2 credit omola_transfer_credit_account_id
        if omola_transfer_credit_account:
            self.omola_transfer_credit_account_id = omola_transfer_credit_account.id
        else:
            self.omola_transfer_credit_account_id = False

        # 3 debit omola_transfer_debit_account_id
        if gomrky_debit_account:
            self.gomrky_debit_account_id = gomrky_debit_account.id
        else:
            self.gomrky_debit_account_id = False
        # 3 credit omola_transfer_credit_account_id
        if gomrky_transfer_credit_account:
            self.gomrky_transfer_credit_account_id = gomrky_transfer_credit_account.id
        else:
            self.gomrky_transfer_credit_account_id = False

        # 4 debit omola_transfer_debit_account_id
        if bhry_transfer_debit_account:
            self.bhry_transfer_debit_account_id = bhry_transfer_debit_account.id
        else:
            self.bhry_transfer_debit_account_id = False
        # 4 credit omola_transfer_credit_account_id
        if bhry_transfer_credit_account:
            self.bhry_transfer_credit_account_id = bhry_transfer_credit_account.id
        else:
            self.bhry_transfer_credit_account_id = False

        # 5 debit
        if tfreegh_debit_account:
            self.tfreegh_debit_account_id = tfreegh_debit_account.id
        else:
            self.tfreegh_debit_account_id = False
        #5 credit
        if tfreegh_credit_account:
            self.tfreegh_credit_account_id = tfreegh_credit_account.id
        else:
            self.tfreegh_credit_account_id = False
        # 6 debit
        if okra_debit_account:
            self.okhra_debit_account_id = okra_debit_account.id
        else:
            self.okhra_debit_account_id = False
        #6 credit
        if okhra_credit_account:
            self.okhra_credit_account_id = okhra_credit_account.id
        else:
            self.okhra_credit_account_id = False

        # end of four accounts
        # end of four accounts
        # end of four accounts
        # end of four accounts
        # end of four accounts

        # 1 debit internal
        if no_internal_account_debit:
            self.no_internal_transfer_debit_account_id = no_internal_account_debit.id
        else:
            self.no_internal_transfer_debit_account_id = False
        # 1 credit internal
        if no_internal_account_credit:
            self.no_internal_transfer_credit_account_id = no_internal_account_credit.id
        else:
            self.no_internal_transfer_credit_account_id = False

        # 2 debit omola_transfer_debit_account_id
        if no_omola_transfer_debit_account:
            self.no_omola_transfer_debit_account_id = no_omola_transfer_debit_account.id
        else:
            self.no_omola_transfer_debit_account_id = False
        # 2 credit omola_transfer_credit_account_id
        if no_omola_transfer_credit_account:
            self.no_omola_transfer_credit_account_id = no_omola_transfer_credit_account.id
        else:
            self.no_omola_transfer_credit_account_id = False

        # 3 debit omola_transfer_debit_account_id
        if no_gomrky_debit_account:
            self.no_gomrky_debit_account_id = no_gomrky_debit_account.id
        else:
            self.no_gomrky_debit_account_id = False
        # 3 credit omola_transfer_credit_account_id
        if no_gomrky_transfer_credit_account:
            self.no_gomrky_transfer_credit_account_id = no_gomrky_transfer_credit_account.id
        else:
            self.no_gomrky_transfer_credit_account_id = False

        # 4 debit omola_transfer_debit_account_id
        if no_bhry_transfer_debit_account:
            self.no_bhry_transfer_debit_account_id = no_bhry_transfer_debit_account.id
        else:
            self.no_bhry_transfer_debit_account_id = False
        # 4 credit omola_transfer_credit_account_id
        if no_bhry_transfer_credit_account:
            self.no_bhry_transfer_credit_account_id = no_bhry_transfer_credit_account.id
        else:
            self.no_bhry_transfer_credit_account_id = False

        # 5 debit
        if no_tfreegh_debit_account:
            self.no_tfreegh_debit_account_id = no_tfreegh_debit_account.id
        else:
            self.no_tfreegh_debit_account_id = False
        # 5 credit
        if no_tfreegh_credit_account:
            self.no_tfreegh_credit_account_id = no_tfreegh_credit_account.id
        else:
            self.no_tfreegh_credit_account_id = False

        # 6 debit
        if no_okra_debit_account:
            self.no_okhra_debit_account_id = no_okra_debit_account.id
        else:
            self.no_okhra_debit_account_id = False
        # 6 credit
        if no_okhra_credit_account:
            self.no_okhra_credit_account_id = no_okhra_credit_account.id
        else:
            self.no_okhra_credit_account_id = False

    def _compute_total_real_cost(self):
        for rec in self:
            sum = 0
            for i in rec.order_line:
                sum += (i.real_price_unit * i.product_qty)
            rec.total_real_cost = sum

    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        self.ensure_one()
        move_type = self._context.get('default_move_type', 'in_invoice')
        journal = self.env['account.move'].with_context(default_move_type=move_type)._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (
                self.company_id.name, self.company_id.id))

        partner_invoice_id = self.partner_id.address_get(['invoice'])['invoice']
        invoice_vals = {
            'ref': self.partner_ref or '',
            'move_type': move_type,
            'narration': self.notes,
            'currency_id': self.currency_id.id,
            'invoice_user_id': self.user_id and self.user_id.id,
            'partner_id': partner_invoice_id,
            'fiscal_position_id': (
                    self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(partner_invoice_id)).id,
            'payment_reference': self.partner_ref or '',
            'partner_bank_id': self.partner_id.bank_ids[:1].id,
            'invoice_origin': self.name,
            'anfas_cost': self.anfas_cost,
            'omola_cost': self.omola_cost,
            'total_real_cost': self.total_real_cost,
            'delevery_date': self.delevery_date,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
        }
        return invoice_vals

    # deleted onchange based on anfas_cost
    # @api.onchange('anfas_cost')
    # def onchange_anfas_cost(self):
    #     if self.amount_total != 0:
    #         cost1 = self.anfas_cost / self.amount_total
    #         for rec in self.order_line:
    #             if cost1 != 0:
    #                 rec.real_price_unit = rec.product_id.standard_price
    #                 rec.price_unit = rec.price_unit * cost1 + rec.price_unit
    #             else:
    #                 rec.price_unit = rec.product_id.standard_price

    @api.onchange('internal_transfer_cost', 'omola_transfer_cost', 'gomrky_cost', 'bhry_cost', 'tfreegh', 'okhra')
    def onchange_set_cost_po_no1(self):
        self.anfas_cost = self.internal_transfer_cost + self.omola_transfer_cost + self.gomrky_cost + self.bhry_cost + self.tfreegh + self.okhra


# po_line
class purchaseOrderLineinherit(models.Model):
    _inherit = 'purchase.order.line'

    product_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True,default=1.0)

    @api.onchange('real_price_unit')
    @api.depends('order_id.anfas_cost', 'real_price_unit')
    def set_real_price_unit(self):
        for rec in self:
            if rec.order_id.anfas_cost == 0:
                rec.price_unit = rec.real_price_unit
            if rec.order_id.amount_total != 0:
                cost1 = rec.order_id.anfas_cost / rec.order_id.amount_total
                if cost1 != 0 and cost1 > 0:
                    rec.price_unit = ((cost1 * rec.price_subtotal) / rec.product_qty) + rec.real_price_unit
                elif cost1 == 0:
                    rec.price_unit = rec.real_price_unit

    real_price_unit = fields.Float('Real Unit Price', required=True, digits='Product Price', default=0.0)
    price_unit = fields.Float(string='Unit Price', required=True, digits='Product Price', compute="set_real_price_unit",
                              readonly=True, store=True)

    # old code
    # @api.onchange('anfas_cost', 'price_unit')
    # def set_real_price_unit(self):
    #     for rec in self:
    #         if rec.price_unit:
    #             rec.real_price_unit = rec.price_unit + self.anfas_cost
    #         else:
    #             rec.real_price_unit = self.anfas_cost
    # real_price_unit = fields.Float('Real Unit Price', required=True, digits='Product Price',default=0.0)

    # @api.onchange('product_id')
    # def onchange_method(self):
    #     self.price_unit = self.product_id.lst_price
    #     self.real_price_unit = self.product_id.standard_price

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
            # 'real_price_unit': self.real_price_unit,

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


# account_move
class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    driver_name = fields.Char(string="اسم السائق", required=False, )
    car_number = fields.Integer(string="رقم السياره", required=False, )
    customer_phone = fields.Integer(string="رقم هاتف الزبون", required=False, )
    customer_adress = fields.Char(string="عنوان الزبون", required=False, )
    anfas_cost = fields.Float(string="التكلفه", required=False, )
    total_real_cost = fields.Float(string="Total Real price", required=False, )
    delevery_date = fields.One2many(comodel_name="dilvevery.date", inverse_name="sale_id", string="", required=False, )
    omola_cost = fields.Float(string="العموله", required=False, )


# account_move_line
class AccountMoveInherit1(models.Model):
    _inherit = 'account.move.line'

    real_price_unit = fields.Float('Real Unit Price', required=True, digits='Product Price', default=0.0)
