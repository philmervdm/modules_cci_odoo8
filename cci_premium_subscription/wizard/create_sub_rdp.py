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
# Version 1.0 Philmer

from openerp import models, fields , api , _ 

import datetime

class wizard_create_subscription_rdp(models.TransientModel):
    _name = 'wizard.create.subscription.rdp'
    
    contact_id = fields.Many2one('res.partner',string='Premium Member', required=True)
    product_id = fields.Many2one('product.product',string='Product',required=True)
    duration = fields.Selection([('year','One Year')], string='Duration', default='year', required=True)
    
    @api.model
    def default_get(self,fields):
        res = super(wizard_create_subscription_rdp, self).default_get(fields)
        if self.env.context.get('active_model') == 'res.partner':
            res['contact_id'] = self.env.context.get('active_id')
        return res
    
    @api.multi
    def second_form(self):
        ctx = self.env.context.copy()
        ctx.update({'contact_id': self.contact_id.id})
        ctx.update({'product_id': self.product_id.id})
        ctx.update({'duration': self.duration})
        value = {
            'domain': [],
            'name': 'Options',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.create.subscription.rdp2',
            'context': ctx,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
        return value
    
class wizard_create_subscription_rdp2(models.TransientModel):
    _name = 'wizard.create.subscription.rdp2'
 
    begin_date =  fields.Date(string='Begin Date', required=True)
    email = fields.Char(string='Specific Email (if asked)',size=250)
    partner_id = fields.Many2one('res.partner',string='Company')
    auto_invoice = fields.Boolean(string = 'Make Invoice')
    
    @api.model
    def default_get(self,fields):
        rec = super(wizard_create_subscription_rdp2, self).default_get(fields)
        
        begin_date = datetime.datetime.today().strftime('%Y-%m-%d')
        # search if existing current mag subscription
        obj_sub_type = self.env['premium_subscription.type']
        type_ids = obj_sub_type.search([('code','=','RDP')]).ids
        if type_ids:
            obj_product = self.env['product.product']
            prod_ids = obj_product.search([('premium_subscription_type_id','in',type_ids)])
            if prod_ids:
                obj_sub = self.env['premium_subscription']
                sub_ids = obj_sub.search([('state','=','current'),('product_id','in',prod_ids.ids)])
                if sub_ids:
                    subs = sub_ids.read(['end'])
                    for subscription in subs:
                        if subscription['end'] >= begin_date:
                            begin_date = datetime.datetime.strptime(subscription['end'], "%Y-%m-%d") + datetime.timedelta(days=1)
                            begin_date = begin_date.strftime('%Y-%m-%d')
        rec['begin_date'] = begin_date
        # search if we have a partner_id to propose by default
        obj_contact = self.env['res.partner']
        contact = obj_contact.browse(self.env.context.get('contact_id',False))
        if contact.other_contact_ids:
            min_seq = 9999
            partner_id = False
            for job in contact.other_contact_ids:
                if job.address_id and job.address_id.partner_id and job.address_id.partner_id.state_id.id == 1:
                    if job.sequence_contact and job.sequence_contact < min_seq:
                        min_seq = job.sequence_contact
                        partner_id = job.address_id.partner_id.id
            if partner_id:
                rec['partner_id'] = contact.parent_id.id
        return rec
    
    @api.multi
    def create_data(self):
        obj_sub = self.env['premium_subscription']
        (new_id_sub,new_id_invoice,msg_final) = obj_sub._create_new_rdp(self.env.context.get('contact_id'),
                                                                  self.env.context.get('product_id'),
                                                                  self.begin_date,
                                                                  self.partner_id.id,
                                                                  self.env.context.get('duration'),
                                                                  self.auto_invoice,
                                                                   self.email)
        if msg_final:
            msg = msg_final
        else:
            msg = 'Finished'
        
        ctx = self.env.context.copy()
        ctx.update({'msg': msg, 'new_id_sub':new_id_sub,
                    'new_id_inv':new_id_invoice, 'auto_inv':self.auto_invoice})
        value = {
            'domain': [],
            'name': 'Notification',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.create.subscription.msg',
            'context': ctx,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
        return value
    
class wizard_create_subscription_msg(models.TransientModel):
    _name = 'wizard.create.subscription.msg'
    
    msg = fields.Text(string='File imported', readonly=True)
    
    @api.model
    def default_get(self,fields):
        rec = super(wizard_create_subscription_msg, self).default_get(fields)
        rec['msg'] = self.env.context.get('msg')
        return rec
    
    @api.multi
    def open_window_subscription(self):
        result = {
            'name': _('Added Subscription'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'premium_subscription',
            'domain': "[('id','=',%s)]" % str(self.env.context.get('new_id_sub')),
            'context': {},
            'type': 'ir.actions.act_window'
        }
        return result
    
    @api.multi
    def open_window_invoice(self):
        result = {
            'name': _('Associated Invoice'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'domain': "[('id','=',%s)]" % str(self.env.context.get('new_id_inv')),
            'context': {},
            'type': 'ir.actions.act_window'
        }
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

