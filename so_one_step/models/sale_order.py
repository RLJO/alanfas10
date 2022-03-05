from odoo import api, fields, models, exceptions


class SaleOrder(models.Model):
    _inherit = "sale.order"

    post_deliver_inv_pick = fields.Boolean(string="Direct POST INVOICE AND Delivery")



    def action_confirm(self):
        imediate_obj = self.env['stock.immediate.transfer']
        res = super(SaleOrder, self).action_confirm()
        for order in self:

            warehouse = order.warehouse_id
            if order.post_deliver_inv_pick and order.picking_ids:
                for picking in self.picking_ids:
                    picking.action_assign()
                    picking.action_confirm()
                    for mv in picking.move_ids_without_package:
                        mv.quantity_done = mv.product_uom_qty
                    picking.button_validate()

            if order.post_deliver_inv_pick and not order.invoice_ids:
                order._create_invoices()

            if order.post_deliver_inv_pick and order.invoice_ids:
                for invoice in order.invoice_ids:
                    invoice.action_post()

        return res
