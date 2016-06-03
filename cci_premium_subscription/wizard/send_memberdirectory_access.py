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

class wizard_send_memberdirectory_access(models.TransientModel):

    _name = 'wizard.send.memberdirectory.access'
    
    forced_address = fields.Char(string='Forced EMail Address',size=250)
    template_id =  fields.Many2one('email.template',string='Email Template',domain=[('model','=','premium_subscription')],required=True)
    
    @api.multi
    def send_mails(self):
        obj_sub = self.env['premium_subscription']
        subs = obj_sub.browse(self.env.context.get('active_ids'))
        msg_final = ''
        
        for subscription in subs:
            # We check if the address(es) are available for management via website
            # and if not, we directly add them before sending mail to user
            obj_user = self.env['res.users']
            user_website_id = obj_user.search([('name','=','Noomia')])[0].id
            modifiable_proxy_ids = []
            full_page_partner_ids = []
            obj_addr_proxy = self.env['directory.address.proxy']
            if subscription.contact_id and subscription.contact_id.other_contact_ids:
#                 for current_job in subscription.contact_id.job_ids:
#                     if current_job.address_id:
                addr_proxy_id = obj_addr_proxy.search([('address_id','=',subscription.contact_id.id)])
                if addr_proxy_id:
                    addr_proxy = addr_proxy_id[0] #obj_addr_proxy.browse(addr_proxy_ids[0])
                    if not addr_proxy.write_uid or (addr_proxy.write_uid and addr_proxy.write_uid.id <> user_website_id and not addr_proxy.user_validated and not addr_proxy.internal_validated):
                        modifiable_proxy_ids.append(addr_proxy.id)
                if subscription.contact_id.parent_id:
                    full_page_partner_ids.append(subscription.contact_id.parent_id.id)

            if subscription.contact_id and subscription.contact_id.other_contact_ids:
#                 for current_job in subscription.contact_id.job_ids:
#                     if current_job.address_id:
                obj_addr_proxy._synchro_address(subscription.contact_id,subscription.contact_id.parent_id,modifiable_proxy_ids,full_page_partner_ids,False,user_website_id,False,False,False,False)
            # get the email address : forced_address; if not : job email; if not personal email
             
            if self.forced_address:
                user_email = self.forced_address or '' 
                 
                if subscription.contact_id:
                    if subscription.contact_id.other_contact_ids and subscription.partner_id:
                        for job in subscription.contact_id.other_contact_ids:
                            if job.address_id and job.address_id.partner_id and job.address_id.partner_id.id == subscription.partner_id.id and job.email:
                                user_email = job.email
                    if not user_email and subscription.contact_id.email:
                        user_email = subscription.contact_id.email

            if self.template_id:
                used_email = obj_sub._send_url(subscription.id,self.template_id.id,user_email)
                if used_email:
                    msg_final += "Send to email '%s'\n" % used_email
                else:
                    msg_final += "Not sended by email because no valid email address was found [%i] \n" % subscription.id
        if msg_final:
            msg = msg_final
        else:
            msg = 'Finished'

        ctx = self.env.context.copy()
        ctx.update({'msg': msg})
        value = {
                'domain': [],
                'name': 'Notification',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'wizard.send.memberdirectory.access.msg',
                'context': ctx,
                'type': 'ir.actions.act_window',
                'target': 'new'
            }
        return value

class wizard_send_memberdirectory_access_msg(models.TransientModel):

    _name = 'wizard.send.memberdirectory.access.msg'
    
    msg = fields.Text(string='File imported', readonly=True)
    
    @api.model
    def default_get(self,fields):
        rec = super(wizard_send_memberdirectory_access_msg, self).default_get(fields)
        rec['msg'] = self.env.context.get('msg')
        return rec

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

