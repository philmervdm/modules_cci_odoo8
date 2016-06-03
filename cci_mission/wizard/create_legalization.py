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
from openerp import models, fields , api , _

class create_legalization(models.TransientModel):
    _name = 'wizard.create.legalization'
    
    leg_type_id = fields.Many2one('cci_missions.dossier_type', string = 'Dossier Type', required = True, domain= "[('section','=','legalization')]")
   
    
    @api.multi
    def create_legalization(self):
        obj_certi = self.env['cci_missions.certificate']
        data_certi = obj_certi.browse(self.env.context.get('active_ids'))
        list_leglization = []
        leg_create = 0
        leg_reject = 0
        leg_rej_reason = ""
        
        type_rec = self.leg_type_id
    
        for data in data_certi:
            leg_create = leg_create + 1
            prod_lines = []
    
            map(lambda x: prod_lines.append(x.id), data.product_ids)
            if data.order_partner_id.membership_state in ('none','canceled'): #the boolean "Apply the member price" should be set to TRUE or FALSE when the partner is changed in regard of the membership state of him.
                is_member = False
            else:
                is_member = True
    
            leg_id = self.env['cci_missions.legalization'].create( {
                'type_id': type_rec.id,
                'date': data.date,
                'order_partner_id': data.order_partner_id.id,
                'quantity_original': data.quantity_original,
                #'text_on_invoice': data.text_on_invoice,
                'asker_name': data.asker_name,
                'sender_name': data.sender_name,
                'state': 'draft',
                'goods': data.goods,
                'goods_value': data.goods_value,
    #            'destination_id': data.destination_id.id, => valid4certificate
                'quantity_copies': 0,
                'quantity_original': 1,
                'to_bill': data.to_bill,
                'member_price': is_member,
                'destination_id': data.destination_id and data.destination_id.id or False,
    #            'product_ids': [(6, 0, prod_lines)] => no need
                })
            self.env.cr.execute('select dossier_id from cci_missions_legalization where id='"'%s'"''%(leg_id.id))
            doss = self.env.cr.fetchone()
            leg_ids = []
            map(lambda x: leg_ids.append(x.id), data.legalization_ids)
            leg_ids.append(leg_id.id)
            data.write({'legalization_ids': [(6, 0, leg_ids)]})
            list_leglization.append(doss)
            
        ctx = self.env.context.copy()
        ctx['leg_created'] = str(leg_create)
        ctx['leg_rejected'] = str(leg_reject)
        ctx['leg_rej_reason'] = leg_rej_reason
        ctx['leg_ids'] = list_leglization
        
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.create.legalization.next',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }

class create_legalization_next(models.TransientModel):
    _name = 'wizard.create.legalization.next'
    
    leg_created = fields.Char(string = 'Legalization Created', readonly = True)
    leg_rejected = fields.Char(string = 'Legalization Rejected', readonly = True)
    leg_rej_reason = fields.Text(string = 'Error Messages', readonly = True)
    
    @api.model
    def default_get(self, fields):
        res = super(create_legalization_next,self).default_get(fields)
        res['leg_created']= self.env.context.get('leg_created')
        res['leg_rejected'] = self.env.context.get('leg_rejected') 
        res['leg_rej_reason'] = self.env.context.get('leg_rej_reason') 
        return res
    
    @api.multi
    def open_leg(self):
        val = {
            'domain': "[('dossier_id','in', ["+','.join(map(str, self.env.context.get('leg_ids')))+"])]",
            'name': 'Legalization',
            'view_type': 'form',
            'view_mode': 'tree, form',
            'res_model': 'cci_missions.legalization',
            'views': [(False, 'tree'), (False, 'form')],
            'type': 'ir.actions.act_window'
            }
        return val

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: