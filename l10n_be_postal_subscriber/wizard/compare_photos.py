# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (c) 2009 CCI  ASBL. (<http://www.ccilconnect.be>).
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

import time
from osv import fields, osv
from openerp import api, fields, models, _

form_confirm = """<?xml version="1.0"?>
<form string="Comparaison entre photos">
    <field name="txtHeader" />
    <newline />
    <field name="date_invoice"/>
    <newline/>
    <field name="period_id"/>
    <newline/>
    <field name="registration"/>
</form>
"""
fields_confirm = {
    'txtHeader' : { 'string' : "Do you want to compare this two photos ?", 'type':'text', 'readonly':True},
    'txtOldPhotoID' : { 'string' : 'Old Photo Name', 'type' : 'text', 'readonly':True},
    'txtNewPhotoID' : { 'string' : 'New Photo Name', 'type' : 'text', 'readonly':True},
    #  'registration': {'string':'Include Events Registrations', 'type':'boolean' ,'default': lambda *a: False },
    #  'date_invoice': {'string':'Date Invoiced', 'type':'date' ,'default': lambda *a: time.strftime('%Y-%m-%d')},
    #  'period_id': {'string':'Force Period (keep empty to use current period)','type':'many2one','relation':'account.period'},
}
form_results = """<?xml version="1.0"?>
<form string="Result of the comparison">
    <separator string="Invoices Grouped for Following Partners." colspan="4" />
    <newline/>
    <field name="message" nolabel="1" colspan="5"/>
</form>
"""
fields_results = {
      'message': {'string':'','type':'text', 'readonly':True, 'size':'500'},
}
@api.multi
def _group_invoice(self, data):
    date_inv = self.date_invoice
    force_period = self.period_id
    today_date = time.strftime('%Y-%m-%d')
    obj_inv = self.env['account.invoice']
    dict_info=[]
    models=['cci_missions.certificate','cci_missions.legalization','cci_missions.embassy_folder','cci_missions.ata_carnet']
    if self.registration:
        models.append('event.registration')

    for model in models:
        if model=='cci_missions.embassy_folder' or model=='event.registration':
            model_ids=self.env[model].search([('state','=','open')])
        else:
            model_ids=self.env[model].search([('state','=','draft')])

        if model_ids:
            read_ids=self.env[model].read(model_ids,['partner_id','order_partner_id','date','creation_date','partner_invoice_id'])
            for element in read_ids:
                part_info={}
                if ('partner_id' in element) and element['partner_id']:
                    part_info['partner_id']=element['partner_id'][0]
                    part_info['id']=element['id']
                    part_info['model']=model

                if ('order_partner_id' in element) and element['order_partner_id']:
                    part_info['partner_id']=element['order_partner_id'][0]
                    part_info['id']=element['id']
                    part_info['model']=model

                if ('partner_invoice_id' in element) and element['partner_invoice_id']:
                    part_info['partner_id']=element['partner_invoice_id'][0]
                    part_info['id']=element['id']
                    part_info['model']=model

                if 'date' in element:
                    part_info['date']=element['date']

                if 'creation_date' in element:
                    part_info['date']=element['creation_date']

                if part_info:
                    dict_info.append(part_info)

    if not dict_info:
        self.invoice_ids=[]
        if self.registration:
            self.message ="No invoices grouped  because no invoices for ATA Carnet, Legalizations, Certifications and (Embassy Folders and Registrations) are in 'Draft' state."
        else:
            self.message="No invoices grouped  because no invoices for ATA Carnet, Legalizations, Certifications and Embassy Folders are in 'Draft' state."
        return self.message

    partner_ids = list(set([x['partner_id'] for x in dict_info]))
    partner_ids.sort()
    disp_msg=''

    list_invoice=[]
    for partner_id in partner_ids:
        partner=self.env['res.partner'].browse(partner_id)
        final_info={}
        list_info=[]
        list_invoice_ids=[]
        self.invoice_info=[]
        for element in dict_info:
            final_info={}
            if element['partner_id']==partner_id:
                data={'model':element['model'],'form':{},'id':element['id'],'ids':[element['id']],'report_type': 'pdf'}
                final_info['ids']=[]
                final_info['date']=element['date'][0:10]

                if element['model']=='cci_missions.ata_carnet':
                    result=create_invoice_carnet._createInvoices(data)

                    if result['inv_rejected']>0 and result['inv_rej_reason']:
                        disp_msg +='\nFor Partner '+ partner.name +' On ATA Carnet with ' + result['inv_rej_reason']
                        continue
                    if result['invoice_ids']:
                        list_invoice_ids.append(result['invoice_ids'][0])
                        final_info['ids'].append(result['invoice_ids'][0])
                        list_info.append(final_info)
                        final_info={}
                        final_info['id']=element['id']
                        final_info['model']=element['model']
                        self.invoice_info.append(final_info)

                if element['model']=='cci_missions.embassy_folder':
                    result=create_invoice_embassy._createInvoices(data)

                    if result['inv_rejected']>0 and result['inv_rej_reason']:
                        disp_msg +='\nFor Partner '+ partner.name +' On Embassy Folder with ' + result['inv_rej_reason']
                        continue
                    if result['invoice_ids']:
                        list_invoice_ids.append(result['invoice_ids'][0])
                        final_info['ids'].append(result['invoice_ids'][0])
                        list_info.append(final_info)
                        final_info={}
                        final_info['id']=element['id']
                        final_info['model']=element['model']
                        self.invoice_info.append(final_info)

                if element['model'] in ('cci_missions.certificate','cci_missions.legalization'):
                    result=create_invoice._createInvoices(data)

                    if result['inv_rejected']>0 and result['inv_rej_reason']:
                        disp_msg +='\nFor Partner '+ partner.name +' On Certificate or Legalization with ' + result['inv_rej_reason']
                        continue
                    if result['invoice_ids']:
                        list_invoice_ids.append(result['invoice_ids'][0])
                        final_info['ids'].append(result['invoice_ids'][0])
                        list_info.append(final_info)
                        final_info={}
                        final_info['id']=element['id']
                        final_info['model']=element['model']
                        self.invoice_info.append(final_info)

                if element['model']=='event.registration':
                    result=make_invoice._makeInvoices(data)

                    if result['inv_rejected']>0 and result['inv_rej_reason']:
                        disp_msg +='\nFor Partner '+ partner.name +' On Event Registration ' + result['inv_rej_reason']
                        continue
                    if result['invoice_ids']:
                        list_invoice_ids.append(result['invoice_ids'][0])
                        final_info['ids'].append(result['invoice_ids'][0])
                        list_info.append(final_info)
                        final_info={}
                        final_info['id']=element['id']
                        final_info['model']=element['model']
                        self.invoice_info.append(final_info)

        done_date=[]
        date_id_dict={}
        done_date=list(set([x['date'] for x in list_info]))
        done_date.sort()
        final_list=[]
        for date in done_date:
            date_id_dict={}
            date_id_dict['date']=date
            date_id_dict['ids']=[]
            for item in list_info:
                if date==item['date']:
                    date_id_dict['ids'] +=item['ids']
            final_list.append(date_id_dict)

        count=0
        list_inv_lines=[]
        #marked

        if not final_list:
            continue
        for record in final_list:
            customer_ref = record['date']
            line_obj = self.env['account.invoice.line']
            id_note=line_obj.create({'name':customer_ref,'state':'title','sequence':count})
            count=count+1
            list_inv_lines.append(id_note)
            data_inv=obj_inv.browse(record['ids'])
            notes = ''
            for invoice in data_inv:
                if invoice.reference:
                    customer_ref = customer_ref +' ' + invoice.reference
                if invoice.comment:
                    notes = (notes + ' ' + invoice.comment)

                for line in invoice.invoice_line:
                    if invoice.name:
                        name = invoice.name +' '+ line.name
                    else:
                        name = line.name
                    #pool_obj.get('account.invoice.line').write(cr,uid,line.id,{'name':name,'sequence':count})
#                    inv_line = line_obj.create(cr, uid, {'name': name,'account_id':line.account_id.id,'price_unit': line.price_unit,'quantity': line.quantity,'discount': False,'uos_id': line.uos_id.id,'product_id':line.product_id.id,'invoice_line_tax_id': [(6,0,line.invoice_line_tax_id)],'note':line.note,'sequence' : count})
                    inv_line = line_obj.create({'name': name,'account_id':line.account_id.id,'price_unit': line.price_unit,'quantity': line.quantity,'discount': False,'uos_id': line.uos_id.id,'product_id':line.product_id.id,'invoice_line_tax_id': [(6,0,line.invoice_line_tax_id)],'note':line.note,'sequence' : count,'cci_special_reference': line.cci_special_reference})
                    count=count+1
                    list_inv_lines.append(inv_line)
    #            If we want to cancel ==> obj_inv.write(cr,uid,invoice.id,{'state':'cancel'}) here
    #            If we want to delete ==> obj_inv.unlink(cr,uid,list_invoice_ids) after new invoice creation.

            line_obj.write(id_note,{'name':customer_ref})
            id_note1=line_obj.create({'name':notes,'state':'text','sequence':count})# a new line of type 'note' with all the old invoice note
            count=count+1
            list_inv_lines.append(id_note1)
            id_linee=line_obj.create({'state':'line','sequence':count}) #a new line of type 'line'
            count=count+1
            list_inv_lines.append(id_linee)
            id_stotal=line_obj.create({'name':'Subtotal','state':'subtotal','sequence':count})#a new line of type 'subtotal'
            count=count+1
            list_inv_lines.append(id_stotal)
        #end-marked
        inv = {
                'name': 'Grouped Invoice - ' + partner.name,
                'origin': 'Grouped Invoice',
                'type': 'out_invoice',
                'reference': False,
                'account_id': invoice.account_id.id,
                'partner_id': invoice.partner_id.id,
                'address_invoice_id':invoice.address_invoice_id.id,
                'address_contact_id':invoice.address_contact_id.id,
                'invoice_line': [(6,0,list_inv_lines)],
                'currency_id' :invoice.currency_id.id,# 1
                'comment': "",
                'payment_term':invoice.payment_term.id,
                'date_invoice':date_inv or today_date,
                'period_id':force_period or False
            }
        inv_id = obj_inv.create(inv)
        for item in self.invoice_info:
            pool_obj.get(item['model']).write([item['id']], {'invoice_id' : inv_id})
        disp_msg +='\n'+ partner.name + ': '+ str(len(data_inv)) +' Invoice(s) Grouped.'
        list_invoice.append(inv_id)
        obj_inv.unlink(list_invoice_ids)
    self.invoice_ids=list_invoice
    self.message=disp_msg
    return data['form']

class wizard_compare_photos(models.TransientModel):
    _name = 'wizard.compare.photos' 
    txtHeader = fields.Text(string= 'Do you want to compare this two photos ?', readonly = True)
    txtOldPhotoID = fields.Text(string = 'Old Photo Name',  readonly = True)
    txtNewPhotoID = fields.Text(string = 'Do you want to compare this two photos ?', readonly = True)
    message = fields.Text(string = 'Message', readonly=True)
    
#    def _capture_ids(self, cr, uid, data, context):
#        print data
#        if len(data['ids']) == 2:
#            # We sort the two IDs to identify the older and the new one and get their name
#            cr.execute( """
#                        SELECT photo.id, photo.name, photo.datetime
#                            FROM dated_photo photo
#                            WHERE photo.id in ( %s, %s )
#                            ORDER by photo.datetime;
#                       """, (data['ids'][0],data['ids'][1]) )
#            photos = cr.fetchall()
#            data['form']['txtOldPhotoID'] = photos[0].name
#            data['form']['txtNewPhotoID'] = photos[1].name
#        else:
#            data['form']['txtHeader'] = "You must choose exactly TWO photos to compare."
#            ## TODO : comment rendre le bouton 'open' indisponible
    @api.multi
    def _compare_photos(data):
        cr.execute( """
                    SELECT partner_id, partner_contact_id, name, title, state_id, street, street2, zip, city
                        FROM l10n_be_postal_subscriber
                        WHERE photo_id = %s
                        ORDER BY partner_id, contact_id;
                    """, photos[0].id )
        old_subs = cr.fetchall()
            
        self.env.cr.execute( """
                    SELECT partner_id, partner_contact_id, name, title, state_id, street, street2, zip, city
                        FROM l10n_be_postal_subscriber
                        WHERE photo_id = %s
                        ORDER BY partner_id, contact_id;
                    """, photos[1].id )
        new_subs = self.env.cr.fetchall()
        
    def _list_results(data):
        pool_obj = self.env['l10n_be_postal_subscriber.photo_diff']
        model_data_ids = self.env['ir.model.data'].search([('model','=','ir.ui.view'),('name','=','invoice_form')])
        resource_id = self.env['ir.model.data'].read(model_data_ids,fields=['res_id'])[0]['res_id']
        return {
            'domain': "[('id','in', ["+','.join(map(str, self.invoice_ids))+"])]",
            'name': 'Invoices',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'views': [(False,'tree'),(resource_id,'form')],
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window'
        }
    states = {
        'init' : {
               'actions' : [],#_capture_ids],
               'result': {'type': 'form', 'arch': form_confirm, 'fields': fields_confirm, 'state':[('open','Yes'),('end','Cancel')]}
            },
        'open': {
            'actions': [_compare_photos],
            'result': {'type':'form', 'arch': form_results, 'fields': fields_results, 'state':[('end','Ok'),('open_res','Open Results')]}
            },
        'open_res': {
            'actions': [],
            'result': {'type':'action', 'action':_list_results, 'state':'end'}
            }
    }
wizard_compare_photos("wizard.compare.photos")
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

#!/usr/bin/env python

