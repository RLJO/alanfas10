from odoo import api, fields, models, _


class purchaseOrderInh(models.Model):
    _inherit = "purchase.order"

    post_deliver_inv_pick = fields.Boolean(string="Direct POST INVOICE AND Delivery")

    #
    def button_confirms(self):
        print("111111111111")
        # imediate_obj = self.env['stock.immediate.transfer']
        warehouse_obj = self.env['stock.warehouse'].search([], limit=1)
        res = super(purchaseOrderInh, self).button_confirm()
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
