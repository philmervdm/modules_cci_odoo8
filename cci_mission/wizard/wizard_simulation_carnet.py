# -*- encoding: utf-8 -*-
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
# version 2.0 : don't create a false ata cranet to simulate, compute directly
from openerp import models, fields, api , _
import time

class compute_ata_price(models.TransientModel):
    _name = 'wizard.compute.ata.price'
    
    type = fields.Many2one('cci_missions.dossier_type', string = 'Type',domain = "[('section','=','ATA')]",required = True)
    creation_date = fields.Date(string = 'Creation Date',required = True, default =time.strftime('%Y-%m-%d'))
    goods_value = fields.Float(string = 'Goods Value', required = True)
    double_signature = fields.Boolean(string = 'Double signature', default = True) 
    member_price = fields.Boolean(string='Member price',help = 'Do we apply member price for the concerned partner ?')
    pages = fields.Integer(string = 'Number of pages')
    own_risk = fields.Boolean(string = 'Own risk', help = 'If not own risk, apply the standard warranty')
    manual_warranty = fields.Float(string = 'Manual warranty',help='Used only if own risk to give the current warranty claimed to the customer')

    @api.multi
    def compute_price(self):
        obj_dossiertype = self.env['cci_missions.dossier_type']
        dossier_type = self.type
        obj_lines = self.env['account.invoice.line']
        #context.update({'pricelist': carnet.partner_id.property_product_pricelist.id})
        prod_list = []
        value = []
        prod_list.append(dossier_type.original_product_id)
        prod_list.append(dossier_type.copy_product_id)
        
        if self.own_risk:
            prod_list.append(dossier_type.warranty_product_1)
        else:
            prod_list.append(dossier_type.warranty_product_2)
            
        ctx = self.env.context.copy()
        ctx.update({'date':self.creation_date})
        count=0
        qty_copy = self.pages
        if qty_copy<0:
           qty_copy=0
        force_member=force_non_member=False
        
        if self.member_price:
            force_member=True
            ptype = 'member_price'
        else:
            force_non_member=True
            ptype = 'list_price'
            
        ctx.update({'partner_id':False})
        ctx.update({'force_member':force_member})
        ctx.update({'force_non_member':force_non_member})
        ctx.update({'value_goods': self.goods_value})
        ctx.update({'double_signature': self.double_signature})
        ctx.update({'date': self.creation_date})
        ctx.update({'emission_date': self.creation_date})
    
        for prod_id in prod_list:
            count +=1
            price = prod_id.with_context(ctx).price_get(ptype)
            value.append(price[prod_id.id])
        sum = value[0]+round(value[1]*qty_copy,2)
        
        if self.own_risk:
            sum += self.manual_warranty
        else:
            sum += value[2]
        message_total = """The final price will be %10.2f euros.
    Don't forget to mention addititional products (like postal costs).""" % (sum)
        ctx['msg'] = message_total
        
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.compute.ata.price.msg',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }

class compute_ata_price_msg(models.TransientModel):
    _name = 'wizard.compute.ata.price.msg'

    msg = fields.Text(string = 'Total Amount to Pay', readonly = True)
    
    @api.model
    def default_get(self, fields):
        res = super(compute_ata_price_msg, self).default_get(fields)
        res.update({'msg': self.env.context.get('msg','')})
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

