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
import wizard
import time
import datetime
import tools
import pooler
from osv import fields
from osv import osv
from tools.translate import _
from dateutil.relativedelta import relativedelta

form = """<?xml version="1.0"?>
<form string="Create Yearly Full Page on App Subscription">
    <field name="contact_id" colspan="4" width="600"/>
    <field name="product_id" colspan="4"/>
</form>"""

fields = {
    'contact_id': {'type':'many2one','relation':'res.partner.contact','domain':"[('is_premium','=','OUI')]",'string':'Premium Member','required':True},
    'product_id': {'type':'many2one','relation':'product.product','domain':"[('premium_subscription_type_id','!=',False)]",'string':'Product','required':True},
}

form2 = """<?xml version="1.0"?>
<form string="Options">
    <field name="begin" />
    <field name="end" />
    <field name="auto_invoice"/>
    <field name="partner_id"/>
    <newline/>
    <field name="send_url"/>
    <newline/>
    <field name="forced_address" colspan="4"/>
    <field name="template_id" colspan="4"/>
</form>"""

fields2 = {
    'begin': {'type':'date','string':'Begin','required':True},
    'end': {'type':'date','string':'End','required':True},
    'auto_invoice': {'type':'boolean','string':'Make Invoice'},
    'partner_id': {'type':'many2one','relation':'res.partner','string':'Partner Invoice'},
    'send_url':  {'type':'boolean','string':'Send URL for Managing Data'},
    'forced_address': {'type':'char','size':250,'string':'Forced EMail Address'},
    'template_id': {'type':'many2one','relation':'cci_email_template','string':'Email Template','domain':"[]"},
}

msg_form = """<?xml version="1.0"?>
<form string="Notification">
     <separator string="Created Record(s)" colspan="4"/>
     <field name="msg" colspan="4" nolabel="1" width="800" heigth="600"/>
</form>"""

msg_fields = {
    'msg': {'string':'Results', 'type':'text', 'readonly':True},
}

class wizard_create_subscription_full_page_from_premium(wizard.interface):

    new_id_sub = False
    new_id_invoice = False
    
    def _set_defaults(self,cr,uid,data,context):
        pool_obj = pooler.get_pool(cr.dbname)
        obj_cont = pool_obj.get('res.partner.contact')
        contact = obj_cont.read(cr,uid,[data['id'],],['is_premium'])[0]
        if contact and contact['is_premium'] == 'OUI':
            data['form']['contact_id'] = data['id']
        return data['form']
        
    def _set_defaults2(self,cr,uid,data,context):
        begin_date = datetime.datetime.today()
        # search if existing current full page subscription
        pool_obj = pooler.get_pool(cr.dbname)
        obj_sub_type = pool_obj.get('premium_subscription.type')
        type_ids = obj_sub_type.search(cr,uid,[('code','=','REPMEMBRE')])
        if type_ids:
            obj_product = pool_obj.get('product.product')
            prod_ids = obj_product.search(cr,uid,[('premium_subscription_type_id','in',type_ids)])
            if prod_ids:
                obj_sub = pool_obj.get('premium_subscription')
                sub_ids = obj_sub.search(cr,uid,[('state','=','current'),('product_id','in',prod_ids),('contact_id','=',data['form']['contact_id'])])
                if sub_ids:
                    subs = obj_sub.read(cr,uid,sub_ids,['end'])
                    for subscription in subs:
                        if subscription['end'] >= begin_date.strftime('%Y-%m-%d'):
                            begin_date = datetime.datetime.strptime(subscription['end'], "%Y-%m-%d") + datetime.timedelta(days=1)
                            begin_date = begin_date
        data['form']['begin'] = begin_date.strftime('%Y-%m-%d')
        data['form']['end'] = (begin_date + datetime.timedelta(days=364) ).strftime('%Y-%m-%d')
        # search if we have a partner_id to propose by default
        obj_contact = pool_obj.get('res.partner.contact')
        contact = obj_contact.browse(cr,uid,data['form']['contact_id'])
        if contact.other_contact_ids:
            min_seq = 9999
            partner_id = False
            for job in contact.other_contact_ids:
                if job.address_id and job.address_id.partner_id and job.address_id.partner_id.state_id.id == 1:
                    if job.sequence_contact and job.sequence_contact < min_seq:
                        min_seq = job.sequence_contact
                        partner_id = job.address_id.partner_id.id
            if partner_id:
                data['form']['partner_id'] = partner_id
        obj_ir_model = pool_obj.get('ir.model')
        ir_model_ids = obj_ir_model.search(cr,uid,[('model','=','premium_subscription')])
        if ir_model_ids:
            fields2['template_id']['domain'] = "[('model_id','=',%i)]" % ir_model_ids[0]
        return data['form']
        
    def _create_data(self,cr,uid,data,context):
        pool_obj=pooler.get_pool(cr.dbname)
        obj_sub = pool_obj.get('premium_subscription')
        (self.new_id_sub,self.new_id_invoice,msg_final) = obj_sub._create_new_full_page(cr,uid,
                                                                                        data['form']['contact_id'],
                                                                                        data['form']['product_id'],
                                                                                        data['form']['begin'],
                                                                                        data['form']['partner_id'],
                                                                                        data['form']['end'],
                                                                                        data['form']['auto_invoice'])
        # We check if the address(es) are available for management via website
        # and if not, we directly add them before sending mail to user
        obj_user = pool_obj.get('res.users')
        user_website_id = obj_user.search(cr,uid,[('name','=','Noomia')])[0]
        new_subscription = obj_sub.browse(cr,uid,self.new_id_sub)
        modifiable_proxy_ids = []
        full_page_partner_ids = []
        obj_addr_proxy = pool_obj.get('directory.address.proxy')
        if new_subscription.contact_id and new_subscription.contact_id.other_contact_ids:
            for current_job in new_subscription.contact_id.other_contact_ids:
                if current_job.address_id:
                    addr_proxy_ids = obj_addr_proxy.search(cr,uid,[('address_id','=',current_job.address_id.id)])
                    if addr_proxy_ids:
                        addr_proxy = obj_addr_proxy.browse(cr,uid,addr_proxy_ids[0])
                        if not addr_proxy.write_uid or (addr_proxy.write_uid and addr_proxy.write_uid.id <> user_website_id and not addr_proxy.user_validated and not addr_proxy.internal_validated):
                            modifiable_proxy_ids.append(addr_proxy.id)
                    if current_job.address_id.partner_id:
                        full_page_partner_ids.append(current_job.address_id.partner_id.id)

        if new_subscription.contact_id and new_subscription.contact_id.other_contact_ids:
            for current_job in new_subscription.contact_id.other_contact_ids:
                if current_job.address_id:
                    obj_addr_proxy._synchro_address(cr,uid,current_job.address_id,current_job.address_id.partner_id,modifiable_proxy_ids,full_page_partner_ids,False,user_website_id,False,False,False,False)
        # get the email address : forced_address; if not : job email; if not personal email
        if data['form']['forced_address']:
            user_email = data['form']['forced_address']
        else:
            user_email = ''
            if new_subscription.contact_id:
                if new_subscription.contact_id.other_contact_ids and new_subscription.partner_id:
                    for job in new_subscription.contact_id.other_contact_ids:
                        if job.address_id and job.address_id.partner_id and job.address_id.partner_id.id == new_subscription.partner_id.id and job.email:
                            user_email = job.email
                if not user_email and new_subscription.contact_id.email:
                    user_email = new_subscription.contact_id.email
        data['form']['msg'] = ''
        if self.new_id_sub and data['form']['send_url'] and user_email:
            if data['form']['template_id']:
                used_email = obj_sub._send_url(cr,uid,self.new_id_sub,data['form']['template_id'],user_email)
                if used_email:
                    data['form']['msg'] = "Send to email '%s'\n" % used_email
                else:
                    data['form']['msg'] = "Not sended by email because no valid email address was found\n"
            else:
                data['form']['msg'] = "Not sended by email because no template given for the email text\n"
        if msg_final:
            data['form']['msg'] += msg_final
        else:
            data['form']['msg'] += 'Finished'
        if not self.new_id_invoice:
            self.states['create']['result']['state'] = [('end','Close'),('show_sub','Show Subscription')]
        return data['form']
    def _open_window_subscription(self, cr, uid, data, context):
        result = {
            'name': _('Added Subscription'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'premium_subscription',
            'domain': "[('id','=',%s)]" % str(self.new_id_sub),
            'context': {},
            'type': 'ir.actions.act_window'
        }
        return result
    def _open_window_invoice(self, cr, uid, data, context):
        result = {
            'name': _('Associated Invoice'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'domain': "[('id','=',%s)]" % str(self.new_id_invoice),
            'context': {},
            'type': 'ir.actions.act_window'
        }
        return result
    states = {
        'init': {
            'actions': [_set_defaults],
            'result': {'type':'form', 'arch':form, 'fields':fields, 'state':[('end','Cancel'),('second_form','Continue')]},
        },
        'second_form': {
            'actions': [_set_defaults2],
            'result': {'type':'form', 'arch':form2, 'fields':fields2, 'state':[('end','Cancel'),('create','Subscribe')]},
        },
        'create': {
            'actions': [_create_data],
            'result': {'type':'form', 'arch':msg_form, 'fields':msg_fields, 'state':[('end','Close'),('show_sub','Show Subscription'),('show_inv','Show Invoice')]}
        },
        'show_sub': {
            'actions': [],
            'result': {'type': 'action', 'action':_open_window_subscription, 'state':'end'}
        },
        'show_inv': {
            'actions': [],
            'result': {'type': 'action', 'action':_open_window_invoice, 'state':'end'}
        },
    }
wizard_create_subscription_full_page_from_premium('wizard_create_sub_full_page_from_premium')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

