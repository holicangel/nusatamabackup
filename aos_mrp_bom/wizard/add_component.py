from odoo import fields,models,api,_

class AddComponent(models.TransientModel):     
     _name = "add.component"
     _description = "Confirm Box"   
        
     name = fields.Char(default="Click The Box If You Wish To Add To BOM Template")
     add_component = fields.One2many('add.product', 'component', 'Add Component')
     
     
     def save_exit(self): 
          ctx = self.env.context.copy()
          lines_ids = ctx.get('active_ids', [])
          mrp_production_obj = self.env['mrp.production'].browse(lines_ids)
          lines_bom = []
          lines_mrp =[]
          for rec in self.add_component : 
               if rec['box'] == True :
               #      if rec.product_id.id in mrp_production_obj.bom_id.bom_line_ids.product_id.ids :
               #           bom_recs = list(mrp_production_obj.bom_id.bom_line_ids.product_id)
               #           # bom_new = rec.product_id
               #           # bom_id = bom_recs.index(rec.product_id)
               #           # id = mrp_production_obj.bom_id.bom_line_ids[bom_id].id
               #           lines_bom.append((0,0,{
               #                "bom_id": mrp_production_obj.bom_id.id,
               #                "product_id" : rec.product_id.id,
               #                "product_uom_id":rec.product_id.uom_id.id,
               #                "product_qty" : rec.product_qty 
               #           }))
               #           # if len(bom_recs[bom_id].bom_line_ids) != 1 :
               #           #      for rec in bom_recs[bom_id].bom_line_ids
               #           #           if rec.id != id :
               #           #           mrp_production_obj.bom_id.write({"bom_line_ids" :newrec})
               #           #      bom_recs[bom_id].bom_line_ids = bom_recs[bom_id].bom_line_ids[0]
               #           lines_mrp.append((0,0,{
               #                "product_id" : rec.product_id.id,
               #                "name":rec.product_id.name,
               #                "product_uom":rec.product_id.uom_id.id,
               #                "location_id":mrp_production_obj.location_src_id.id,
               #                "location_dest_id":rec.product_id.property_stock_production.id,
               #                "product_uom_qty" : rec.product_qty,
               #                "group_id" : mrp_production_obj.procurement_group_id.id,
               #                "company_id" : mrp_production_obj.company_id.id,
               #                "procure_method" : "make_to_order",
               #                "warehouse_id": mrp_production_obj.move_raw_ids[0].warehouse_id.id,
               #                "picking_type_id" : mrp_production_obj.picking_type_id.id,
               #     }))
               #      else :
                         lines_bom.append((0,0,{
                              "bom_id": mrp_production_obj.bom_id.id,
                              "product_id" : rec.product_id.id,
                              "product_uom_id":rec.product_id.uom_id.id,
                              "product_qty" : rec.product_qty
                         }))
                         lines_mrp.append((0,0,{
                              "product_id" : rec.product_id.id,
                              "name":rec.product_id.name,
                              "product_uom":rec.product_id.uom_id.id,
                              "location_id":mrp_production_obj.location_src_id.id,
                              "location_dest_id":rec.product_id.property_stock_production.id,
                              "product_uom_qty" : rec.product_qty,
                              "group_id" : mrp_production_obj.procurement_group_id.id,
                              "company_id" : mrp_production_obj.company_id.id,
                              "procure_method" : "make_to_order",
                              "warehouse_id": mrp_production_obj.move_raw_ids[0].warehouse_id.id,
                              "picking_type_id" : mrp_production_obj.picking_type_id.id,
                   }))
               else :      
                    lines_mrp.append((0,0,{
                        "product_id" : rec.product_id.id,
                        "name":rec.product_id.name,
                        "product_uom":rec.product_id.uom_id.id,
                        "location_id":mrp_production_obj.location_src_id.id,
                        "location_dest_id":rec.product_id.property_stock_production.id,
                        "product_uom_qty" : rec.product_qty,
                        "group_id" : mrp_production_obj.procurement_group_id.id,
                        "company_id" : mrp_production_obj.company_id.id,
                        "warehouse_id": mrp_production_obj.move_raw_ids[0].warehouse_id.id,
                        "procure_method" : "make_to_order",
                        "picking_type_id" : mrp_production_obj.picking_type_id.id,
                   }))
          if lines_bom:
               # for item in lines_bom :
               #      tuprec = tuple(item)
               #      newrec = [tuprec]
               #      if item[2]['product_id'] in list(mrp_production_obj.bom_id.bom_line_ids.product_id.ids) :
               #           add_bom = mrp_production_obj.bom_id.update({"bom_line_ids" :newrec})
               #      else:
               add_bom = mrp_production_obj.bom_id.update({"bom_line_ids" :lines_bom})
               if mrp_production_obj.state != 'draft':
                    mrp_line = mrp_production_obj.update({"move_raw_ids" :lines_mrp})
                    mrp_production_obj.move_raw_ids._action_confirm()
               else :
                    mrp_line = mrp_production_obj.update({"move_raw_ids" :lines_mrp})
               return add_bom , mrp_line
          else:
               if mrp_production_obj.state != 'draft':
                    mrp_line = mrp_production_obj.update({"move_raw_ids" :lines_mrp})
                    mrp_production_obj.move_raw_ids._action_confirm()
               else : 
                    mrp_line = mrp_production_obj.update({"move_raw_ids" :lines_mrp})
               return mrp_line

class AddProduct(models.TransientModel):
     _name ="add.product"
     _description ="Add Product"
     product_id = fields.Many2one("product.product", "Product")
     component = fields.Many2one("add.component")
     product_qty = fields.Integer(string="Qty")
     box = fields.Boolean()