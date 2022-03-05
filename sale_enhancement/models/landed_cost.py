# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, fields, models, tools, _


class AdjustmentLinesInherit(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'
    _description = 'Valuation Adjustment Lines changes'

    one_unit_cost = fields.Float(string="سعر الوحده بعد التكلفه", compute="set_quantity_one_unit_cost")

    @api.depends('final_cost','quantity')
    def set_quantity_one_unit_cost(self):
        for rec in self:
            if rec.final_cost and rec.quantity:
                if rec.quantity != 0.0:
                   rec.one_unit_cost = rec.final_cost / rec.quantity
