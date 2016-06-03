##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################


from openerp import models, fields , api , _

class product_supplierinfo(models.Model):
    _inherit = 'product.supplierinfo'


    @api.multi
    def _last_order(self):
        res = {}
        for supinfo in self:
            self._cr.execute("select po.id, max(po.date_approve) from purchase_order as po, purchase_order_line as line where po.id=line.order_id and line.product_id=%s and po.partner_id=%s and po.state='approved' group by po.id", (supinfo.product_tmpl_id.id, supinfo.name.id,))
            record = self._cr.fetchone()
            if record:
                res[supinfo.id] = record[0]
            else:
                res[supinfo.id] = False
        return res


    @api.multi
    def _last_order_date(self):
        res = {}
        po = self.env['purchase.order']
        last_orders = self._last_order()
        dates = po.read(filter(None, last_orders.values()), ['date_approve'])
        for suppinfo in self:
            date_approve = [x['date_approve'] for x in dates if x['id']==last_orders[suppinfo]]
            if date_approve:
                res[suppinfo] = date_approve[0]
            else:
                res[suppinfo] = False
        return res

    last_order =  fields.Many2one('purchase.order', compute=_last_order, string='Last Order')
    last_order_date = fields.Date(compute=_last_order_date, string='Last Order date')


class product_product(models.Model):
    _inherit = 'product.product'
    
    def _find_op(self, cr, uid, ids, name, arg, context):
        res = {}
        for product_id in ids:
            cr.execute('SELECT swo.id from stock_warehouse_orderpoint AS swo WHERE product_id=%s', (product_id,))
            op_id = cr.fetchone()
            if op_id:
                res[product_id] = op_id[0]
            else:
                res[product_id] = False
        return res

    @api.multi
    def _product_dispo(self):
        for p_id in self:
            p_id.qty_dispo = self.outgoing_qty + self.qty_available

    calculate_price = fields.Boolean('Compute standard price', help="Check this box if the standard price must be computed from the BoM.")
    orderpoint_ids = fields.One2many('stock.warehouse.orderpoint', 'product_id', string='Orderpoints')
    qty_dispo = fields.Float(compute='_product_dispo', string='Stock available')


    @api.multi
    def compute_price(self):
        bom_obj = self.env['mrp.bom']
        for prod_id in self:
            bom_ids = bom_obj.search([('product_id', '=', prod_id.id)])
            if bom_ids:
                for bom in bom_ids:
                    self._calc_price(bom)
        return True
                    
    def _calc_price(self, bom):
        uom_obj = self.env['product.uom']
        bom_obj = self.env['mrp.bom']

        if not bom.product_id.calculate_price:
            return bom.product_id.standard_price
        else:
            price = 0
            if bom.bom_lines:
                for sbom in bom.bom_lines:
                    price += self._calc_price(sbom) * sbom.product_qty                    
            else:
                no_child_bom = bom_obj.search([('product_id', '=', bom.product_id.id), ('bom_id', '=', False)])
                if no_child_bom and bom.id not in no_child_bom:
                    other_bom = bom_obj.browse(no_child_bom)[0]
                    if not other_bom.product_id.calculate_price:
                        price += self._calc_price(other_bom) * other_bom.product_qty
                    else:
#                        price += other_bom.product_qty * other_bom.product_id.standard_price
                        price += other_bom.product_id.standard_price
                else:
#                    price += bom.product_qty * bom.product_id.standard_price
                    price += bom.product_id.standard_price
#                if no_child_bom:
#                    other_bom = bom_obj.browse(cr, uid, no_child_bom)[0]
#                    price += bom.product_qty * self._calc_price(cr, uid, other_bom)
#                else:
#                    price += bom.product_qty * bom.product_id.standard_price
            if bom.routing_id:
                for wline in bom.routing_id.workcenter_lines:
                    wc = wline.workcenter_id
                    cycle = wline.cycle_nbr
                    hour = (wc.time_start + wc.time_stop + cycle * wc.time_cycle) *  (wc.time_efficiency or 1.0)
                    price += wc.costs_cycle * cycle + wc.costs_hour * hour
                    price = uom_obj._compute_price(bom.product_uom.id,price,bom.product_id.uom_id.id)
            if bom.bom_lines:
                bom.product_id.write({'standard_price' : price/bom.product_qty})
            if bom.product_uom.id != bom.product_id.uom_id.id:
                price = uom_obj._compute_price(bom.product_uom.id,price,bom.product_id.uom_id.id)
            return price


class product_bom(models.Model):
    _inherit = 'mrp.bom'
            
    standard_price = fields.Float(related='product_id.standard_price', string="Standard Price", store=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

