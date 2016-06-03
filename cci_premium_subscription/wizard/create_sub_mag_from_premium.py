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
<form string="Create Yearly CCI Mag Subscription">
    <field name="contact_id" colspan="4" width="600"/>
    <field name="product_id" colspan="4"/>
    <field name="duration" />
</form>"""

fields = {
    'contact_id': {'type':'many2one','relation':'res.partner.contact','domain':"[('is_premium','=','OUI')]",'string':'Premium Member','required':True},
    'product_id': {'type':'many2one','relation':'product.product','domain':"[('premium_subscription_type_id','!=',False)]",'string':'Product','required':True},
    'duration': {'type':'selection','string':'Duration','selection':[('year','One Year (10 issues)')],'default':'year','required':True},
}

form2 = """<?xml version="1.0"?>
<form string="Options">
    <field name="begin_date" />
    <field name="first_issue_id"/>
    <field name="auto_invoice" />
    <field name="partner_id"/>
</form>"""

fields2 = {
    'begin_date': {'type':'date','string':'Begin Date','required':True},
    'partner_id': {'type':'many2one','relation':'res.partner','string':'Company'},
    'first_issue_id':{'type':'many2one','relation':'sale.advertising.issue','string':'First Issue Manualy Sended'},
    'auto_invoice': {'type':'boolean','string':'Make Invoice'},
}

msg_form = """<?xml version="1.0"?>
<form string="Notification">
     <separator string="Created Record(s)" colspan="4"/>
     <field name="msg" colspan="4" nolabel="1" width="800" heigth="600"/>
</form>"""

msg_fields = {
    'msg': {'string':'File imported', 'type':'text', 'readonly':True},
}

class wizard_create_subscription_mag_from_premium(wizard.interface):

    new_id_sub = False
    new_id_invoice = False
    
    def _set_defaults(self,cr,uid,data,context):
        data['form']['contact_id'] = data['id']
        return data['form']
        
    def _set_defaults2(self,cr,uid,data,context):
        begin_date = datetime.datetime.today().strftime('%Y-%m-%d')
        # search if existing current mag subscription
        pool_obj=pooler.get_pool(cr.dbname)
        obj_sub_type = pool_obj.get('premium_subscription.type')
        type_ids = obj_sub_type.search(cr,uid,[('code','=','CCIMAG')])
        if type_ids:
            obj_product = pool_obj.get('product.product')
            prod_ids = obj_product.search(cr,uid,[('premium_subscription_type_id','in',type_ids)])
            if prod_ids:
                obj_sub = pool_obj.get('premium_subscription')
                sub_ids = obj_sub.search(cr,uid,[('state','=','current'),('product_id','in',prod_ids),('left_usages','>',0)])
                if sub_ids:
                    subs = obj_sub.read(cr,uid,sub_ids,['end'])
                    for subscription in subs:
                        if subscription['end'] >= begin_date:
                            begin_date = datetime.datetime.strptime(subscription['end'], "%Y-%m-%d") + datetime.timedelta(days=1)
                            begin_date = begin_date.strftime('%Y-%m-%d')
        data['form']['begin_date'] = begin_date
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
        return data['form']
        
    def _create_data(self,cr,uid,data,context):
        pool_obj=pooler.get_pool(cr.dbname)
        obj_sub = pool_obj.get('premium_subscription')
        (self.new_id_sub,self.new_id_invoice,msg_final) = obj_sub._create_new(cr,uid,
                                                                               data['form']['contact_id'],
                                                                               data['form']['product_id'],
                                                                               data['form']['begin_date'],
                                                                               data['form']['partner_id'],
                                                                               data['form']['duration'],
                                                                               data['form']['first_issue_id'],
                                                                               data['form']['auto_invoice'])
        if msg_final:
            data['form']['msg'] = msg_final
        else:
            data['form']['msg'] = 'Finished'
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

wizard_create_subscription_mag_from_premium('wizard_create_sub_mag_from_premium')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

