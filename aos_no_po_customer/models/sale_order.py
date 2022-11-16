"""
- sale.order
"""
from odoo import models, fields,api
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'




    no_po = fields.Char(string="No Pesanan",required=False)


    def action_confirm(self):
        if not self.no_po:
            raise UserError("No Pesanan is required and cannot empty")

        return super(SaleOrder,self).action_confirm()