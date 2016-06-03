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

class wizard_create_subscription_full_page_premium(models.TransientModel):
    _name= 'wizard.create.subscription.full.page.premium'
    
    contact_id = fields.Many2one('res.partner',string='Premium Member', required=True)
    product_id = fields.Many2one('product.product',string='Product',required=True)

    @api.model
    def default_get(self,fields):
        res = super(wizard_create_subscription_full_page_premium, self).default_get(fields)
        if self.env.context.get('active_model') == 'res.partner':
            res['contact_id'] = self.env.context.get('active_id')
        return res
    
    @api.multi
    def second_form(self):
        ctx = self.env.context.copy()
        ctx.update({'contact_id': self.contact_id.id})
        ctx.update({'product_id': self.product_id.id})
        value = {
            'domain': [],
            'name': 'Options',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.create.subscription.full.page.premium2',
            'context': ctx,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
        return value
    
class wizard_create_subscription_full_page_premium2(models.TransientModel):
    _name= 'wizard.create.subscription.full.page.premium2'
    
    begin =  fields.Date(string='Begin Date', required=True)
    end =  fields.Date(string='End Date', required=True)
    auto_invoice = fields.Boolean(string = 'Make Invoice')
    partner_id = fields.Many2one('res.partner',string='Partner Invoice')
    send_url =  fields.Boolean(string = 'Send URL for Managing Data')
    forced_address = fields.Char(size=250,string='Forced EMail Address')    
    template_id =  fields.Many2one('email.template', string='Email Template', domain=[('model','=','premium_subscription')])

    @api.model
    def default_get(self,fields):
        rec = super(wizard_create_subscription_full_page_premium2, self).default_get(fields)
        
        begin_date = datetime.datetime.today()#.strftime('%Y-%m-%d')
        # search if existing current mag subscription
        obj_sub_type = self.env['premium_subscription.type']
        type_ids = obj_sub_type.search([('code','=','REPMEMBRE')]).ids
        if type_ids:
            obj_product = self.env['product.product']
            prod_ids = obj_product.search([('premium_subscription_type_id','in',type_ids)])
            if prod_ids:
                obj_sub = self.env['premium_subscription']
                sub_ids = obj_sub.search([('state','=','current'),('product_id','in',prod_ids.ids),('contact_id','=', self.env.context.get('contact_id'))])
                if sub_ids:
                    subs = sub_ids.read(['end'])
                    for subscription in subs:
                        if subscription['end'] >= begin_date:
                            begin_date = datetime.datetime.strptime(subscription['end'], "%Y-%m-%d") + datetime.timedelta(days=1)
#                             begin_date = begin_date.strftime('%Y-%m-%d')
                            
        rec['begin'] = begin_date.strftime('%Y-%m-%d')
        rec['end'] = (begin_date + datetime.timedelta(days=364) ).strftime('%Y-%m-%d')
        # search if we have a partner_id to propose by default
        obj_contact = self.env['res.partner']
        contact = obj_contact.browse(self.env.context.get('contact_id',False))
        if contact.other_contact_ids:
            min_seq = 9999
            partner_id = False
            for job in contact.other_contact_ids:
                if job.address_id and job.address_id.parent_id and job.address_id.parent_id.state_id.id == 1:
                    if job.sequence_contact and job.sequence_contact < min_seq:
                        min_seq = job.sequence_contact
                        partner_id = job.address_id.parent_id.id
            if partner_id:
                rec['partner_id'] = contact.parent_id.id
        return rec

    @api.multi
    def create_data(self):
        obj_sub = self.env['premium_subscription']
        (new_id_sub,new_id_invoice,msg_final) = obj_sub._create_new_full_page(self.env.context.get('contact_id'),
                                                                                self.env.context.get('product_id'),
                                                                                self.begin,
                                                                                self.partner_id.id,
                                                                                self.end,
                                                                                self.auto_invoice)
        # We check if the address(es) are available for management via website
        # and if not, we directly add them before sending mail to user
        obj_user = self.env['res.users']
        user_website_id = obj_user.search([('name','=','Noomia')])[0]
        new_subscription = obj_sub.browse(new_id_sub)
        modifiable_proxy_ids = []
        full_page_partner_ids = []
        obj_addr_proxy = self.env['directory.address.proxy']
         
        if new_subscription.contact_id and new_subscription.contact_id.other_contact_ids:
            for current_job in new_subscription.contact_id.other_contact_ids:
                addr_proxy = obj_addr_proxy.search([('address_id','=',current_job.address_id.id)])
                if addr_proxy:
                    addr_proxy = addr_proxy[0] #addr_proxy_ids.browse(cr,uid,addr_proxy_ids[0])
                    if not addr_proxy.write_uid or (addr_proxy.write_uid and addr_proxy.write_uid.id <> user_website_id and not addr_proxy.user_validated and not addr_proxy.internal_validated):
                        modifiable_proxy_ids.append(addr_proxy.id)
                if new_subscription.contact_id.parent_id:
                    full_page_partner_ids.append(new_subscription.contact_id.parent_id.id)
                         
        if new_subscription.contact_id and new_subscription.contact_id.other_contact_ids:
            for current_job in new_subscription.contact_id.other_contact_ids:
                if current_job.address_id:
                    obj_addr_proxy._synchro_address(new_subscription.contact_id,new_subscription.contact_id.parent_id,modifiable_proxy_ids,full_page_partner_ids,False,user_website_id,False,False,False,False)
        
        # get the email address : forced_address; if not : job email; if not personal email
        if self.forced_address:
            user_email = self.forced_address
        else:
            user_email = ''
            if new_subscription.contact_id:
                if new_subscription.contact_id.other_contact_ids and new_subscription.partner_id:
                    for job in new_subscription.contact_id.other_contact_ids:
                        if job.address_id and job.address_id.parent_id and job.address_id.parent_id.id == new_subscription.partner_id.id and job.email:
                            user_email = job.email
                if not user_email and new_subscription.contact_id.email:
                    user_email = new_subscription.contact_id.email
        
        msg = ''
        if new_id_sub and self.send_url and user_email:
            if self.template_id:
                used_email = obj_sub._send_url(new_id_sub,self.template_id.id,user_email)
                if used_email:
                    msg = "Send to email '%s'\n" % used_email
                else:
                    msg = "Not sended by email because no valid email address was found\n"
            else:
                msg = "Not sended by email because no template given for the email text\n"
        
        if msg_final:
            msg += msg_final
        else:
            msg += 'Finished'
            
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
    
class wizard_create_subscription_full_page_msg(models.TransientModel):
    _name= 'wizard.create.subscription.full.page.msg'    
    
    msg = fields.Text(string='File imported', readonly=True)
    
    @api.model
    def default_get(self,fields):
        rec = super(wizard_create_subscription_full_page_msg, self).default_get(fields)
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

