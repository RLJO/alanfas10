# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        default=lambda self: self.env['stock.picking.type'].browse(
            self._context.get('default_picking_type_id')).default_location_dest_id,
        check_company=True, readonly=True, required=True,
        states={'draft': [('readonly', False)], 'assigned': [('readonly', False)], 'confirmed': [('readonly', False)]})

    @api.model
    def default_get(self, default_fields):
        res = super(StockPicking, self).default_get(default_fields)
        if self.env.user.branch_id:
            res.update({
                'branch_id': self.env.user.branch_id.id or False
            })
        return res

    branch_id = fields.Many2one('res.branch', string="Branch")
